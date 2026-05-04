import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

import pytest
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from realview_chat.api.backend.app import app as flask_app
from realview_chat.database import db
from realview_chat.database.models import Case, Image
from datetime import datetime



@pytest.fixture(scope="session")
def app():
    flask_app.config.update({
        "TESTING": True,
    })

    with flask_app.app_context():
        db.init_db()

    yield flask_app


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function", autouse=True)
def clean_db(app):
    with app.app_context():
        session = db.SessionLocal()

        try:
            for table in reversed(db.Base.metadata.sorted_tables):
                session.execute(table.delete())
            session.commit()
        finally:
            session.close()

