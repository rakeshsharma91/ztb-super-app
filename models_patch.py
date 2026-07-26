# models_patch.py — run once to migrate the DB
from sqlalchemy import text
from app import app, db

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE user_responses ADD COLUMN is_complete BOOLEAN DEFAULT 0"))
            print("Added is_complete column")
        except Exception as e:
            print(f"is_complete already exists or error: {e}")
        try:
            conn.execute(text("ALTER TABLE user_responses ADD COLUMN last_question_index INTEGER DEFAULT 0"))
            print("Added last_question_index column")
        except Exception as e:
            print(f"last_question_index already exists or error: {e}")
        conn.commit()
        print("Migration complete.")
