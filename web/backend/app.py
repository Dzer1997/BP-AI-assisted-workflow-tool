import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy.orm import joinedload

from realview_chat.config import Settings
from realview_chat.database import db
from realview_chat.database.db import SessionLocal, init_db
from realview_chat.database.models import Case, Feedback, FeedbackFeature, FeedbackScore

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = PROJECT_ROOT / "out"
FEEDBACK_PATH = OUT_DIR / "feedback.json"
GROUND_TRUTH_DIR = OUT_DIR / "ground_truth"

CASES_ROOT = PROJECT_ROOT / "cases"

app = Flask(__name__)
CORS(app)
init_db()

@app.route("/api/properties", methods=["GET"])
def get_properties():
    db = SessionLocal()

    cases = db.query(Case).all()

    properties = []
    
    for case in cases:
        images_list = []
        rooms_list = []

        for r in case.pass25_results:
                rooms_list.append({
                    "room_type": r.room_type,
                    "room_condition_score": r.condition_score,
                    "room_modernity_score": r.modernity_score,
                    "room_material_score": r.material_score,
                    "room_functionality_score": r.functionality_score,
                    "confidence": r.confidence
                })

        for img in case.images:
            p2 = img.pass2_result
            pass2_features = []
            p1 = img.pass1_result
            pass1_data = None
            if p1:
                pass1_data = {
                    "room_type": p1.room_type,
                    "actionable": p1.actionable,
                    "confidence": p1.pass1_confidence,
            }

            if p2:
                for f in p2.features:
                    pass2_features.append({
                        "feature_id": f.feature_id,
                        "severity": f.severity,
                        "confidence": f.confidence,
                        "explanation": f.explanation
                    })

            images_list.append({
                "filename": img.file_path,
                "pass1": pass1_data,
                "pass2":pass2_features
            })
                
        properties.append({
            "property_id": case.folder_name,
            "created_at": case.created_at.isoformat(),
            "images": images_list,  
            "rooms": rooms_list   
        })

    db.close()
    return jsonify(properties)


@app.route("/api/images/<property_id>/<path:filename>", methods=["GET"])
def serve_image(property_id, filename):
    case_folder = CASES_ROOT / f"case_{property_id}"

    if not case_folder.exists():
        abort(404, description="Case not found")

    file_path = case_folder / filename

    if not file_path.exists():
        abort(404, description="Image not found")
    
    return send_from_directory(case_folder, filename)

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    db = SessionLocal()

    feedback_entries = db.query(Feedback).all()

    result = []

    for fb in feedback_entries:
        result.append({
            "property_id": fb.property_id,
            "filename": fb.filename,
            "classification": fb.classification
        })

    db.close()
    return jsonify(result)
    

@app.route("/api/feedback", methods=["POST"])
def post_feedback():
    db = SessionLocal()

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    for field in ("property_id", "filename"):
        if field not in body:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    has_classification = "classification" in body
    has_verdict = "feature_id" in body and "verdict" in body
    has_score = "score_type" in body and "value" in body

    if not has_classification and not has_verdict and not has_score:
        return jsonify({"error": "Invalid feedback type"}), 400

    if has_classification:
        if body["classification"] not in ["correct", "fp", "fn"]:
            return jsonify({"error": "Invalid classification"}), 400

    if has_score:
        if body["score_type"] not in ["condition", "modernity", "material", "functionality"]:
            return jsonify({"error": "Invalid score_type"}), 400

        try:
            value = int(body["value"])
        except:
            return jsonify({"error": "value must be int"}), 400

        if value < 1 or value > 5:
            return jsonify({"error": "value must be between 1 and 5"}), 400

    fb = Feedback(
        property_id=body["property_id"],
        filename=body["filename"],
        classification=body.get("classification")
    )

    db.add(fb)
    db.flush()  

    if has_score:
        score = FeedbackScore(
            feedback_id=fb.id,
            score_type=body["score_type"],
            value=value
        )
        db.add(score)

    if has_verdict:
        feat = FeedbackFeature(
            feedback_id=fb.id,
            feature_id=body["feature_id"],
            verdict=body["verdict"]
        )
        db.add(feat)

    db.commit()
    db.close()

    if body.get("classification") == "correct":
        _copy_to_ground_truth(body["property_id"], body["filename"])

    return jsonify({"ok": True, "entry": body}), 201


def _copy_to_ground_truth(property_id: str, filename: str) -> None:
    base = Path(filename).name
    case_folder = property_id if str(property_id).startswith("case_") else f"case_{property_id}"
    src = CASES_ROOT / case_folder / base

    if not src.exists() or not src.is_file():
        app.logger.warning("Ground truth copy skipped – source not found: %s", src)
        return

    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    dest = GROUND_TRUTH_DIR / f"{property_id}_{base}"
    try:
        shutil.copy2(src, dest)
        app.logger.info("Copied to ground truth: %s -> %s", src, dest)
    except OSError as exc:
        app.logger.error("Failed to copy to ground truth: %s", exc)


def _load_ai_scores() -> dict[tuple[str, str], dict[str, int | None]]:
    ai_scores: dict[tuple[str, str], dict[str, int | None]] = {}
    for path in OUT_DIR.glob("results_*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        pid = str(data.get("property_id", ""))
        for img in data.get("images", []):
            fname = img.get("filename", "")
            ai_scores[(pid, fname)] = {
                "condition": img.get("condition_score"),
                "modernity": img.get("modernity_score"),
                "material": img.get("material_score"),
                "functionality": img.get("functionality_score"),
            }
    return ai_scores


SCORE_TYPES = ("condition", "modernity", "material", "functionality")


def _compute_calibration(feedback: list[dict], ai_scores: dict) -> dict:
    latest_human: dict[tuple[str, str, str], int] = {}
    for entry in feedback:
        st = entry.get("score_type")
        val = entry.get("value")
        if st and val is not None:
            key = (entry["property_id"], entry["filename"], st)
            latest_human[key] = int(val)

    diffs: dict[str, list[int]] = {st: [] for st in SCORE_TYPES}

    for (pid, fname, score_type), human_val in latest_human.items():
        if score_type not in diffs:
            continue
        ai_vals = ai_scores.get((pid, fname))
        if not ai_vals:
            continue
        ai_val = ai_vals.get(score_type)
        if ai_val is None:
            continue
        diffs[score_type].append(human_val - ai_val)

    result: dict[str, dict] = {}
    for score_type in SCORE_TYPES:
        d = diffs[score_type]
        n = len(d)
        if n == 0:
            result[score_type] = {
                "pairs": 0,
                "mae": None,
                "bias": None,
                "agreement_rate": None,
            }
        else:
            mae = sum(abs(v) for v in d) / n
            bias = sum(d) / n
            agree = sum(1 for v in d if v == 0)
            result[score_type] = {
                "pairs": n,
                "mae": round(mae, 2),
                "bias": round(bias, 2),
                "agreement_rate": round(agree / n * 100, 1),
            }

    all_diffs = [v for st in SCORE_TYPES for v in diffs[st]]
    n_all = len(all_diffs)
    if n_all > 0:
        result["overall"] = {
            "pairs": n_all,
            "mae": round(sum(abs(v) for v in all_diffs) / n_all, 2),
            "bias": round(sum(all_diffs) / n_all, 2),
            "agreement_rate": round(sum(1 for v in all_diffs if v == 0) / n_all * 100, 1),
        }
    else:
        result["overall"] = {"pairs": 0, "mae": None, "bias": None, "agreement_rate": None}

    return result


GRADE_SCALE = [
    (17, "A", "Ny/eksklusiv"),
    (13, "B", "Pæn og moderne"),
    (9, "C", "Brugbar/neutral"),
    (5, "D", "Forældet/slidt"),
    (0, "E", "Renoveringskrævende"),
]


def _total_to_grade(total: int) -> tuple[str, str]:
    for threshold, letter, label in GRADE_SCALE:
        if total >= threshold:
            return letter, label
    return "E", "Renoveringskrævende"


@app.route("/api/stats", methods=["GET"])
def get_stats():
    feedback = db.query(Feedback).all()

    latest = {}

    # dedup gem kun en entry
    # sidste skriver over de tidligere
    for fb in feedback:
        key = (fb.property_id, fb.filename)
        value = fb.classification
        latest[key] = value

    correct = sum(1 for v in latest.values() if v == "correct")
    fp = sum(1 for v in latest.values() if v == "fp")
    fn = sum(1 for v in latest.values() if v == "fn")

    precision = (correct / (correct + fp) * 100) if (correct + fp) > 0 else 0
    recall = (correct / (correct + fn) * 100) if (correct + fn) > 0 else 0
    
    ai_scores = _load_ai_scores()
    calibration = _compute_calibration(feedback, ai_scores)

    db.close()

    return jsonify({
        "correct": correct,
        "fp": fp,
        "fn": fn,
        "total_classified": correct + fp + fn,
        "precision": round(precision, 1),
        "recall": round(recall, 1),
        "calibration": calibration,
    })


@app.route("/api/reset", methods=["DELETE"])
def reset_benchmarking():
    db = SessionLocal()

    db.query(FeedbackScore).delete()
    db.query(FeedbackFeature).delete()
    db.query(Feedback).delete()
    db.commit()

    db.close()

    try:
        if GROUND_TRUTH_DIR.exists():
            shutil.rmtree(GROUND_TRUTH_DIR)
        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return jsonify({"error": f"Failed to clear ground truth: {e}"}), 500

    return jsonify({"ok": True})


@app.route("/api/ground_truth", methods=["GET"])
def get_ground_truth():
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}
    files = []
    for p in sorted(GROUND_TRUTH_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in image_extensions:
            files.append(p.name)
    return jsonify(files)


@app.route("/api/ground_truth/<path:filename>", methods=["GET"])
def serve_ground_truth_image(filename):
    base = Path(filename).name
    if base != filename:
        return jsonify({"error": "Invalid filename"}), 400
    path = GROUND_TRUTH_DIR / base
    if not path.exists() or not path.is_file():
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(str(GROUND_TRUTH_DIR), base)


@app.route("/api/summary", methods=["GET"])
def get_summary():
    db = SessionLocal()

    try:
        cases = db.query(Case).all()

        total_images = 0
        kitchen_count = 0
        bathroom_count = 0
        kb_actionable = 0
        kb_total = 0
        feature_counter: Counter[str] = Counter()
        proposal_image_counts: list[int] = []

        severity_counter: Counter[str] = Counter()
        kitchen_damage: Counter[str] = Counter()
        bathroom_damage: Counter[str] = Counter()

        p1_confidence_sum = 0.0
        p1_confidence_n = 0
        p2_confidence_sum = 0.0
        p2_confidence_n = 0

        property_damage: dict[str, dict[str, int]] = {}
        property_room_grades: list[dict] = []

        for case in cases:

            prop_id = case.folder_name
            images = case.images
            proposal_image_counts.append(len(images))
            total_images += len(images)
            prop_high = 0
            prop_total_dmg = 0

            for img in images:
                p1 = img.pass1_result
                room_type = None
                actionable = False
                if p1:
                    room_type = p1.room_type
                    actionable = p1.actionable

                p1_conf = p1.pass1_confidence if p1 else None
                if p1_conf is not None:
                    p1_confidence_sum += p1_conf
                    p1_confidence_n += 1

                if room_type == "kitchen":
                    kitchen_count += 1
                    kb_total += 1
                    if actionable:
                        kb_actionable += 1
                elif room == "bathroom":
                    bathroom_count += 1
                    kb_total += 1
                    if actionable:
                        kb_actionable += 1

                p2 = img.pass2_result
                if p2:
                    for feature in p2.features:
                        fid = feature.feature_id
                        
                        if not fid:
                            continue

                        feature_counter[fid] += 1
                        prop_total_dmg += 1

                        sev = (feature.severity or "").lower()
                        if sev:
                            severity_counter[sev] += 1
                        if sev == "high":
                            prop_high += 1

                        if room == "kitchen":
                            kitchen_damage[fid] += 1
                        elif room == "bathroom":
                            bathroom_damage[fid] += 1

                        p2_conf = feature.confidence
                        if p2_conf is not None:
                            p2_confidence_sum += p2_conf
                            p2_confidence_n += 1

                property_damage[prop_id] = {"high": prop_high, "total": prop_total_dmg}

                rooms_graded = []
                for room in case.pass25_results:
                    scores = {
                        "condition": room.condition_score,
                        "modernity": room.modernity_score,
                        "material": room.material_score,
                        "functionality": room.functionality_score,
                    }
                    values = [v for v in scores.values() if v is not None]
                    if len(values) == 4:
                        total = sum(values)
                        grade, grade_label = _total_to_grade(total)
                        rooms_graded.append({
                            "room_type": room.room_type or "unknown",
                            **scores,
                            "total": total,
                            "grade": grade,
                            "grade_label": grade_label,
                        })
                if rooms_graded:
                    property_room_grades.append({
                        "property_id": prop_id,
                        "rooms": rooms_graded,
                    })

            actionability_rate = (kb_actionable / kb_total * 100) if kb_total > 0 else 0
            num_proposals = len(proposal_image_counts)
            avg_images = (total_images / num_proposals) if num_proposals > 0 else 0

            at_risk = sorted(
                property_damage.items(),
                key=lambda kv: (-kv[1]["high"], -kv[1]["total"]),
            )[:5]
    finally:
        db.close()

    return jsonify({
        "pipeline_funnel": {
            "total_images": total_images,
            "kitchen_or_bathroom": kitchen_count + bathroom_count,
        },
        "room_distribution": {
            "kitchen": kitchen_count,
            "bathroom": bathroom_count,
        },
        "damage_frequency": [
            {"feature_id": fid, "count": cnt}
            for fid, cnt in feature_counter.most_common()
        ],
        "room_damage_profiles": {
            "kitchen": [
                {"feature_id": fid, "count": cnt}
                for fid, cnt in kitchen_damage.most_common()
            ],
            "bathroom": [
                {"feature_id": fid, "count": cnt}
                for fid, cnt in bathroom_damage.most_common()
            ],
        },
        "severity_breakdown": {
            "high": severity_counter.get("high", 0),
            "medium": severity_counter.get("medium", 0),
            "low": severity_counter.get("low", 0),
        },
        "confidence_metrics": {
            "pass1_avg": round(p1_confidence_sum / p1_confidence_n, 3) if p1_confidence_n else None,
            "pass1_count": p1_confidence_n,
            "pass2_avg": round(p2_confidence_sum / p2_confidence_n, 3) if p2_confidence_n else None,
            "pass2_count": p2_confidence_n,
        },
        "at_risk_properties": [
            {
                "property_id": pid,
                "high_severity_count": counts["high"],
                "total_damage_count": counts["total"],
            }
            for pid, counts in at_risk
            if counts["high"] > 0
        ],
        "actionability_rate": {
            "actionable_kb_images": kb_actionable,
            "total_kb_images": kb_total,
            "rate_percent": round(actionability_rate, 1),
        },
        "per_proposal_stats": {
            "num_proposals": num_proposals,
            "total_images": total_images,
            "avg_images_per_proposal": round(avg_images, 1),
        },
        "room_grades": property_room_grades,
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)