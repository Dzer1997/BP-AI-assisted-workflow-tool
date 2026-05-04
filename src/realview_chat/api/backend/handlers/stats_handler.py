from flask import jsonify

from realview_chat.database import db
from realview_chat.database.models import Feedback
from realview_chat.services.analysis_service import _load_ai_scores, compute_stats


def get_stats_handler():
    session = db.SessionLocal()

    try:
        feedback = session.query(Feedback).all()
        
        ai_scores = _load_ai_scores()

        result = compute_stats(feedback, ai_scores)

        return jsonify(result)

    finally:
        session.close()