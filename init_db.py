# init_db.py — Database initialization script for ZTB Super App
import os  # import os for environment variable access
import psycopg2  # import psycopg2 for direct PostgreSQL connection
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT  # import autocommit for CREATE DATABASE
from dotenv import load_dotenv  # import dotenv to load .env file
from werkzeug.security import generate_password_hash  # import password hasher

load_dotenv()  # load environment variables from .env file

# --- Read database config from environment ---
DB_HOST = os.environ.get('DB_HOST', 'localhost')  # PostgreSQL host
DB_PORT = os.environ.get('DB_PORT', '5432')  # PostgreSQL port
DB_NAME = os.environ.get('DB_NAME', 'ztb_db')  # target database name
DB_USER = os.environ.get('DB_USER', 'ztb_user')  # database user
DB_PASS = os.environ.get('DB_PASS', 'ztb_pass123')  # database password
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'ZTBranch2026!')  # default admin password

def create_database_if_not_exists():
    """Connect to postgres maintenance DB and create ztb_db if it doesn't exist."""
    print(f"[1/5] Checking if database '{DB_NAME}' exists...")  # log step
    conn = psycopg2.connect(  # connect to the default 'postgres' maintenance database
        host=DB_HOST,  # host
        port=DB_PORT,  # port
        dbname='postgres',  # maintenance database
        user=DB_USER,  # user
        password=DB_PASS  # password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # set autocommit for DDL
    cur = conn.cursor()  # create cursor
    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))  # check if DB exists
    exists = cur.fetchone()  # fetch result
    if not exists:  # if database does not exist
        cur.execute(f"CREATE DATABASE {DB_NAME}")  # create the database
        print(f"[1/5] ✅ Database '{DB_NAME}' created.")  # log success
    else:
        print(f"[1/5] ✅ Database '{DB_NAME}' already exists.")  # log already exists
    cur.close()  # close cursor
    conn.close()  # close connection

def create_tables():
    """Use SQLAlchemy + Flask app context to create all tables."""
    print("[2/5] Creating all tables via SQLAlchemy...")  # log step
    from app import create_app  # import app factory
    from models import db  # import db instance
    app = create_app()  # create Flask app
    with app.app_context():  # push app context
        db.create_all()  # create all tables defined in models.py
        print("[2/5] ✅ All tables created.")  # log success
    return app  # return app for reuse

def seed_admin_password(app):
    """Seed the AdminConfig table with the default hashed admin password."""
    print("[3/5] Seeding admin password...")  # log step
    from models import db, AdminConfig  # import models
    with app.app_context():  # push app context
        existing = AdminConfig.query.filter_by(key='admin_password').first()  # check if already seeded
        if not existing:  # if not seeded yet
            hashed = generate_password_hash(ADMIN_PASSWORD)  # hash the admin password
            record = AdminConfig(key='admin_password', value=hashed)  # create record
            db.session.add(record)  # add to session
            db.session.commit()  # commit to database
            print(f"[3/5] ✅ Admin password seeded.")  # log success
        else:
            print(f"[3/5] ✅ Admin password already seeded.")  # log already seeded

def seed_column_definitions(app):
    """Seed default column definitions for each library table."""
    print("[4/5] Seeding default column definitions...")  # log step
    from models import db, ColumnDefinition  # import models

    # --- Default columns for each library table ---
    defaults = {
        'valueprop': [  # Value Propositions library columns
            ('vp_name', 'Value Prop Name', 'text', True, 1),  # name column
            ('use_case', 'Use Case', 'text', True, 2),  # use case column
            ('technical_use_case', 'Technical Use Case', 'text', True, 3),  # technical use case
            ('business_outcome', 'Business Outcome', 'text', True, 4),  # business outcome
            ('notes', 'Notes', 'text', False, 5),  # notes column
        ],
        'asset': [  # Assets library columns
            ('asset_name', 'Asset Name', 'text', True, 1),  # asset name
            ('asset_type', 'Asset Type', 'text', True, 2),  # asset type
            ('url', 'URL', 'text', True, 3),  # asset URL
            ('description', 'Description', 'text', False, 4),  # description
            ('notes', 'Notes', 'text', False, 5),  # notes
        ],
        'testcase': [  # Test Cases library columns
            ('test_name', 'Test Name', 'text', True, 1),  # test name
            ('category', 'Category', 'text', True, 2),  # category
            ('steps', 'Steps', 'text', True, 3),  # test steps
            ('expected_result', 'Expected Result', 'text', True, 4),  # expected result
            ('notes', 'Notes', 'text', False, 5),  # notes
        ],
        'roadblock': [  # Roadblocks library columns
            ('roadblock_name', 'Roadblock', 'text', True, 1),  # roadblock name
            ('category', 'Category', 'text', True, 2),  # category
            ('mitigation', 'Mitigation', 'text', True, 3),  # mitigation strategy
            ('severity', 'Severity', 'text', True, 4),  # severity level
            ('notes', 'Notes', 'text', False, 5),  # notes
        ],
        'povplanner': [  # POV Planner library columns
            ('activity', 'Activity', 'text', True, 1),  # activity name
            ('owner', 'Owner', 'text', True, 2),  # activity owner
            ('due_date', 'Due Date', 'text', True, 3),  # due date
            ('status', 'Status', 'text', True, 4),  # status
            ('notes', 'Notes', 'text', False, 5),  # notes
        ],
        'question': [  # Questions library columns
            ('question_text', 'Question', 'text', True, 1),  # question text
            ('question_type', 'Type', 'text', True, 2),  # question type
            ('section', 'Section', 'text', True, 3),  # section
            ('display_order', 'Order', 'number', True, 4),  # display order
            ('is_active', 'Active', 'boolean', True, 5),  # active flag
        ],
    }

    with app.app_context():  # push app context
        for table_name, columns in defaults.items():  # loop through each table
            for col_key, col_label, col_type, required, order in columns:  # loop through columns
                existing = ColumnDefinition.query.filter_by(  # check if already exists
                    table_name=table_name, column_key=col_key
                ).first()
                if not existing:  # if not seeded
                    col_def = ColumnDefinition(  # create column definition
                        table_name=table_name,  # table name
                        column_key=col_key,  # column key
                        column_label=col_label,  # display label
                        column_type=col_type,  # data type
                        is_required=required,  # required flag
                        display_order=order,  # display order
                        is_active=True  # active by default
                    )
                    db.session.add(col_def)  # add to session
        db.session.commit()  # commit all column definitions
        print("[4/5] ✅ Default column definitions seeded.")  # log success

def print_summary():
    """Print a final summary of what was done."""
    print("[5/5] ✅ Database initialization complete!")  # log complete
    print("="*50)  # separator
    print("ZTB Super App — Database Ready")  # title
    print(f"  Host:     {DB_HOST}:{DB_PORT}")  # print host
    print(f"  Database: {DB_NAME}")  # print database name
    print(f"  User:     {DB_USER}")  # print user
    print("  Tables:   admin_config, user_responses, column_definitions,")  # list tables
    print("            value_props, assets, test_cases, roadblocks,")  # more tables
    print("            pov_planners, questions, question_options, assessment_rows")  # more tables
    print("  Admin:    Password seeded (use ADMIN_PASSWORD env var to change)")  # admin info
    print("="*50)  # separator

if __name__ == '__main__':  # run only when executed directly
    create_database_if_not_exists()  # step 1: create database
    app = create_tables()  # step 2: create all tables
    seed_admin_password(app)  # step 3: seed admin password
    seed_column_definitions(app)  # step 4: seed column definitions
    print_summary()  # step 5: print summary
