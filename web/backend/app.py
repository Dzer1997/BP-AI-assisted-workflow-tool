from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from realview_chat.config import init_config
from realview_chat.database import db
from realview_chat.services.analysis_service import get_ground_truth_handler, reset_benchmarking_handler, serve_ground_truth_image_handler, serve_image_handler
from realview_chat.observability.logging_config import init_request_logging
from web.backend.handlers.feedback_handlers import get_feedback_handler, post_feedback_handler
from web.backend.handlers.properties_handlers import get_properties_handler
from web.backend.handlers.stats_handler import get_stats_handler
from web.backend.handlers.summary_handler import get_summary_handler
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from realview_chat.observability.metrics import HTTP_REQUESTS_TOTAL, REQUEST_DURATION



PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = Flask(__name__)
CORS(app)

init_config()
db.init_db()

init_request_logging(app)

@app.route("/api/properties", methods=["GET"])
def get_properties():
    return jsonify(get_properties_handler())


@app.route("/api/images/<property_id>/<path:filename>", methods=["GET"])
def serve_image(property_id,filename):
    return serve_image_handler(property_id, filename)

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
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(port=5001, debug=True)