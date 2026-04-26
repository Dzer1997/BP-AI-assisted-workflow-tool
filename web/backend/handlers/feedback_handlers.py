from flask import jsonify, request

from realview_chat.database import db
from realview_chat.services.analysis_service import _copy_to_ground_truth, post_feedback, get_feedback


def get_feedback_handler():
    session = db.SessionLocal()

    try:
        result = get_feedback(session)
        return jsonify(result)

    finally:
        session.close()

def post_feedback_handler():
    session = db.SessionLocal()

    try:
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

        value = None

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

        fb = post_feedback(
            session,
            body,
            value,
            has_score,
            has_verdict,
            has_classification
        )

        session.commit()

        if body.get("classification") == "correct":
            _copy_to_ground_truth(body["property_id"], body["filename"])

        return jsonify({
            "ok": True,
            "id": fb.id
        }), 201

    finally:
        session.close()


