"""
Run once to add question_category_types table
and category_type_id column to questions.
Usage: python3 migrate_category_type.py
"""
import sqlalchemy as sa
from app import app, db

with app.app_context():
    engine    = db.engine
    inspector = sa.inspect(engine)
    existing  = inspector.get_table_names()

    with engine.connect() as conn:

        # 1. Create question_category_types table if missing
        if 'question_category_types' not in existing:
            conn.execute(sa.text("""
                CREATE TABLE question_category_types (
                    id         SERIAL PRIMARY KEY,
                    name       VARCHAR(255) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            print('[migration] Created table: question_category_types')
        else:
            print('[migration] Table already exists: question_category_types')

        # 2. Add category_type_id column to questions if missing
        q_cols = [c['name'] for c in inspector.get_columns('questions')]
        if 'category_type_id' not in q_cols:
            conn.execute(sa.text("""
                ALTER TABLE questions
                ADD COLUMN category_type_id INTEGER
                REFERENCES question_category_types(id)
                ON DELETE SET NULL
            """))
            print('[migration] Added column: questions.category_type_id')
        else:
            print('[migration] Column already exists: questions.category_type_id')

        conn.commit()
        print('[migration] Done!')
