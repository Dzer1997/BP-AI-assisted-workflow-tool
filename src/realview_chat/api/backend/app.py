from pathlib import Path
from flask import Flask, Response, abort, jsonify, send_file
from flask_cors import CORS
from realview_chat.config import CASES_ROOT, init_config
from realview_chat.database import db
from realview_chat.services.analysis_service import get_ground_truth_handler, reset_benchmarking_handler, serve_ground_truth_image_handler
from realview_chat.observability.logging_config import init_request_logging
from realview_chat.api.backend.handlers.feedback_handlers import get_feedback_handler, post_feedback_handler
from realview_chat.api.backend.handlers.properties_handlers import get_properties_handler
from realview_chat.api.backend.handlers.stats_handler import get_stats_handler
from realview_chat.api.backend.handlers.summary_handler import get_summary_handler
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = Flask(__name__)
CORS(app)

init_config()
db.init_db()

init_request_logging(app)

@app.route("/api/properties", methods=["GET"])
def get_properties():
    return jsonify(get_properties_handler())

@app.route("/api/images/<path:filepath>")
def serve_image(filepath):
    file_path = CASES_ROOT / f"case_{filepath}"

    if not file_path.exists():
        abort(404)

    return send_file(file_path)

@app.route("/api/feedback", methods=["GET"])
def get_feedback():
    return get_feedback_handler()
    
@app.route("/api/feedback", methods=["POST"])
def post_feedback():
    return post_feedback_handler()
    
@app.route("/api/stats", methods=["GET"])
def get_stats():
    return get_stats_handler()


@app.route("/api/reset", methods=["DELETE"])
def reset_benchmarking():
    return reset_benchmarking_handler()

@app.route("/api/ground_truth", methods=["GET"])
def get_ground_truth():
    return get_ground_truth_handler()

@app.route("/api/ground_truth/<path:filename>", methods=["GET"])
def serve_ground_truth_image(filename):
    return serve_ground_truth_image_handler(filename)

@app.route("/api/summary", methods=["GET"])
def get_summary():
    return get_summary_handler()

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)