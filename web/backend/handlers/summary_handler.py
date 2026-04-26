from flask import jsonify

from realview_chat.database import db
from realview_chat.database.models import Case
from realview_chat.services.analysis_service import _total_to_grade, compute_summary


def get_summary_handler():
    session = db.SessionLocal()

    try:
        cases = session.query(Case).all()
        return jsonify(compute_summary(cases,_total_to_grade))

    finally:
        session.close()