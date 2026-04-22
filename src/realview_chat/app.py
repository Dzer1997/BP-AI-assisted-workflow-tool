from pathlib import Path
import sys
import time

from realview_chat.database.db import SessionLocal, init_db
from realview_chat.pipeline.property_processor import process_property_from_folder
from realview_chat.config import load_config
from realview_chat.openai_client.responses import create_client
from realview_chat.database.models import Case
from realview_chat.services.db_mapper import save_case_to_db

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CASES_ROOT = PROJECT_ROOT / "cases"


def run_scan_mode(client, db, delay_seconds=4, limit=None):
    case_folders = sorted(
        p for p in CASES_ROOT.iterdir()
        if p.is_dir() and p.name.startswith("case_")
    )

    print(f"Found {len(case_folders)} cases")

    processed_count = 0

    for path in case_folders:
        if limit is not None and processed_count >= limit:
            print(f"Reached limit of {limit} cases. Stopping.")
            break

        property_id = path.name.replace("case_", "", 1)

        existing_case = db.query(Case).filter_by(folder_name=property_id).first()
        if existing_case:
            print(f"Skipping {property_id} (already processed)")
            continue

        print(f"Processing case: {property_id}")

        try:
            result = process_property_from_folder(
                images_dir=path,
                property_id=property_id,
                client=client,
            )

            save_case_to_db(db, result)

            print(f"Saved case {property_id} to database.")
            processed_count += 1

        except Exception as e:
            db.rollback()
            print(f"Error processing {property_id}: {e}")
            continue

        print(f"Sleeping for {delay_seconds} seconds...")
        time.sleep(delay_seconds)

    print(f"Done. Processed {processed_count} new cases.")


def main():
    init_db()
    print("Database initialized successfully.")

    db = SessionLocal()

    try:
        config = load_config()
        client = create_client(config)
        print(f"Initialized client with model: {config.openai_model}")

        run_scan_mode(client, db)

    except ValueError as e:
        sys.exit(f"Configuration Error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    main()