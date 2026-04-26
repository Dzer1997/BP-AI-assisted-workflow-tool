from realview_chat.database import db
from realview_chat.services.analysis_service import get_properties


def get_properties_handler():
    session = db.SessionLocal()

    try:
        result = get_properties(session)
        return result

    finally:
        session.close()