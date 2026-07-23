from app import app, db
from sqlalchemy import text
from models import ColumnDefinition

SCHEMA = {
    "value_props": [
        ("value_prop_name",    "Value Prop Name",       True,  "TEXT"),
        ("use_case",           "Use Case",              False, "TEXT"),
        ("technical_use_case", "Technical Use Case",    False, "TEXT"),
        ("business_outcome",   "Business Outcome",      False, "TEXT"),
        ("mandatory",          "Mandatory",             False, "BOOLEAN DEFAULT FALSE"),
    ],
    "assets": [
        ("asset_name",          "Asset Name",           True,  "TEXT"),
        ("description",         "Description",          False, "TEXT"),
        ("link",                "Link",                 False, "TEXT"),
        ("detailed_explanation","Detailed Explanation",  False, "TEXT"),
        ("mandatory",           "Mandatory",            False, "BOOLEAN DEFAULT FALSE"),
        ("how_it_uses_asset",   "How It Uses Asset",    False, "TEXT"),
    ],
    "test_cases": [
        ("test_case_name", "Test Case Name", True,  "TEXT"),
        ("test_steps",     "Test Steps",     False, "TEXT"),
        ("in_scope",       "In Scope",       False, "TEXT"),
        ("result",         "Result",         False, "TEXT"),
        ("notes",          "Notes",          False, "TEXT"),
        ("mandatory",      "Mandatory",      False, "BOOLEAN DEFAULT FALSE"),
    ],
    "pov_planner": [
        ("milestone_step", "Milestone / Step",      True,  "TEXT"),
        ("status",         "Status",                False, "TEXT"),
        ("target_start",   "Target Start",          False, "TEXT"),
        ("target_end",     "Target End",            False, "TEXT"),
        ("what_it_proves", "What It Proves / Notes",False, "TEXT"),
        ("mandatory",      "Mandatory",             False, "BOOLEAN DEFAULT FALSE"),
    ],
    "roadblocks": [
        ("issue_name",        "Issue Name",         True,  "TEXT"),
        ("status",            "Status",             False, "TEXT"),
        ("jira_feature_link", "JIRA Feature Link",  False, "TEXT"),
        ("explanation",       "Explanation",        False, "TEXT"),
        ("mandatory",         "Mandatory",          False, "BOOLEAN DEFAULT FALSE"),
    ],
}

def run():
    with app.app_context():
        for table, cols in SCHEMA.items():
            print(f"\n--- {table} ---")
            existing = {r[0] for r in db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name=:t"),
                {"t": table}).fetchall()}
            for i, (key, label, required, col_type) in enumerate(cols):
                if key not in existing:
                    try:
                        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {key} {col_type}"))
                        db.session.commit()
                        print(f"  + Added DB column: {key}")
                    except Exception as e:
                        db.session.rollback()
                        print(f"  ! Failed to add {key}: {e}")
                else:
                    print(f"  ✓ Exists in DB: {key}")
                if not ColumnDefinition.query.filter_by(table_name=table, column_key=key).first():
                    db.session.add(ColumnDefinition(
                        table_name=table, column_key=key, column_label=label,
                        column_type='boolean' if 'BOOLEAN' in col_type else 'text',
                        display_order=i, is_active=True, is_required=required))
                    db.session.commit()
                    print(f"  + Seeded ColumnDefinition: {label}")
                else:
                    print(f"  ✓ ColumnDefinition exists: {label}")
        print("\n✅ Migration complete!")

if __name__ == '__main__':
    run()
