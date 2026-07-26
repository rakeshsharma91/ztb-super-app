from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ─────────────────────────────────────────
# ADMIN USER
# ─────────────────────────────────────────
class Admin(db.Model):
    __tablename__ = 'admins'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password      = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────
# ADMIN CONFIG
# ─────────────────────────────────────────
class AdminConfig(db.Model):
    __tablename__ = 'admin_config'
    id         = db.Column(db.Integer, primary_key=True)
    key        = db.Column(db.String(255), unique=True, nullable=False)
    value      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# COLUMN DEFINITION
# ─────────────────────────────────────────
class ColumnDefinition(db.Model):
    __tablename__ = 'column_definitions'
    id            = db.Column(db.Integer, primary_key=True)
    table_name    = db.Column(db.String(100), nullable=False)
    column_key    = db.Column(db.String(100), nullable=False)
    column_label  = db.Column(db.String(255), nullable=False)
    column_type   = db.Column(db.String(50), default='text')
    display_order = db.Column(db.Integer, default=0)
    is_active     = db.Column(db.Boolean, default=True)
    is_required   = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('table_name', 'column_key', name='uq_table_column'),
    )

# ─────────────────────────────────────────
# VALUE PROPS
# ─────────────────────────────────────────
class ValueProp(db.Model):
    __tablename__ = 'value_props'
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text)
    business_value = db.Column(db.String(100))
    mandatory      = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# ASSETS
# ─────────────────────────────────────────
class Asset(db.Model):
    __tablename__ = 'assets'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    asset_type  = db.Column(db.String(100))
    url         = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────
class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(255), nullable=False)
    description     = db.Column(db.Text)
    steps           = db.Column(db.Text)
    expected_result = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# POV PLANNER
# ─────────────────────────────────────────
class POVPlanner(db.Model):
    __tablename__ = 'pov_planner'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration    = db.Column(db.String(100))
    owner       = db.Column(db.String(100))
    status      = db.Column(db.String(50), default='Pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# ROADBLOCKS
# ─────────────────────────────────────────
class Roadblock(db.Model):
    __tablename__ = 'roadblocks'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category    = db.Column(db.String(100))
    severity    = db.Column(db.String(50))
    mitigation  = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ─────────────────────────────────────────
# QUESTION CATEGORY
# ─────────────────────────────────────────
class QuestionCategory(db.Model):
    __tablename__ = 'question_categories'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(255), nullable=False, unique=True)
    order      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions  = db.relationship('Question', backref='category_ref', lazy=True,
                                  cascade='all, delete-orphan')

# ─────────────────────────────────────────
# QUESTIONS
# ─────────────────────────────────────────
class Question(db.Model):
    __tablename__ = 'questions'
    id           = db.Column(db.Integer, primary_key=True)
    category_id  = db.Column(db.Integer, db.ForeignKey('question_categories.id'), nullable=False)
    text         = db.Column(db.Text, nullable=False)
    options_type = db.Column(db.String(50), default='select_one')
    order        = db.Column(db.Integer, default=0)
    info_only    = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    options      = db.relationship('QuestionOption', backref='question', lazy=True,
                                    cascade='all, delete-orphan')

# ─────────────────────────────────────────
# M2M ASSOCIATION TABLES
# ─────────────────────────────────────────
option_assets = db.Table(
    'option_assets',
    db.Column('id',        db.Integer, primary_key=True),
    db.Column('option_id', db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False),
    db.Column('asset_id',  db.Integer, db.ForeignKey('assets.id',           ondelete='CASCADE'), nullable=False),
    db.UniqueConstraint('option_id', 'asset_id', name='uq_opt_asset'),
)

option_valueprops = db.Table(
    'option_valueprops',
    db.Column('id',            db.Integer, primary_key=True),
    db.Column('option_id',     db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False),
    db.Column('value_prop_id', db.Integer, db.ForeignKey('value_props.id',      ondelete='CASCADE'), nullable=False),
    db.UniqueConstraint('option_id', 'value_prop_id', name='uq_opt_vp'),
)

option_testcases = db.Table(
    'option_testcases',
    db.Column('id',           db.Integer, primary_key=True),
    db.Column('option_id',    db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False),
    db.Column('test_case_id', db.Integer, db.ForeignKey('test_cases.id',       ondelete='CASCADE'), nullable=False),
    db.UniqueConstraint('option_id', 'test_case_id', name='uq_opt_tc'),
)

option_povsteps = db.Table(
    'option_povsteps',
    db.Column('id',          db.Integer, primary_key=True),
    db.Column('option_id',   db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False),
    db.Column('pov_step_id', db.Integer, db.ForeignKey('pov_planner.id',      ondelete='CASCADE'), nullable=False),
    db.UniqueConstraint('option_id', 'pov_step_id', name='uq_opt_pov'),
)

option_roadblocks = db.Table(
    'option_roadblocks',
    db.Column('id',           db.Integer, primary_key=True),
    db.Column('option_id',    db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False),
    db.Column('roadblock_id', db.Integer, db.ForeignKey('roadblocks.id',       ondelete='CASCADE'), nullable=False),
    db.UniqueConstraint('option_id', 'roadblock_id', name='uq_opt_rb'),
)

# ─────────────────────────────────────────
# QUESTION OPTIONS
# ─────────────────────────────────────────
class QuestionOption(db.Model):
    __tablename__ = 'question_options'
    id          = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    label       = db.Column(db.String(255), nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    assets      = db.relationship('Asset',      secondary='option_assets',     lazy='subquery')
    value_props = db.relationship('ValueProp',  secondary='option_valueprops', lazy='subquery')
    test_cases  = db.relationship('TestCase',   secondary='option_testcases',  lazy='subquery')
    pov_steps   = db.relationship('POVPlanner', secondary='option_povsteps',   lazy='subquery')
    roadblocks  = db.relationship('Roadblock',  secondary='option_roadblocks', lazy='subquery')

    def to_dict(self):
        return {
            'id':            self.id,
            'question_id':   self.question_id,
            'option_text':   self.label,
            'asset_ids':     [a.id for a in self.assets],
            'valueprop_ids': [v.id for v in self.value_props],
            'testcase_ids':  [t.id for t in self.test_cases],
            'povstep_ids':   [p.id for p in self.pov_steps],
            'roadblock_ids': [r.id for r in self.roadblocks],
        }

# ─────────────────────────────────────────
# ASSESSMENT CONFIG
# ─────────────────────────────────────────
class AssessmentConfig(db.Model):
    __tablename__ = 'assessment_config'
    id            = db.Column(db.Integer, primary_key=True)
    question_id   = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    is_active     = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    question      = db.relationship('Question', backref=db.backref('assessment_configs', cascade='all, delete-orphan'), lazy=True)

    def to_dict(self):
        return {
            'id':            self.id,
            'question_id':   self.question_id,
            'is_active':     self.is_active,
            'display_order': self.display_order,
            'created_at':    self.created_at.isoformat() if self.created_at else None,
            'updated_at':    self.updated_at.isoformat() if self.updated_at else None,
        }

# ─────────────────────────────────────────
# USER RESPONSE
# ─────────────────────────────────────────
class UserResponse(db.Model):
    __tablename__ = 'user_responses'
    id            = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    se_name       = db.Column(db.String(255), nullable=False)
    started_at    = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at  = db.Column(db.DateTime, nullable=True)
    answers       = db.Column(db.JSON, default=dict)
    results       = db.Column(db.JSON, default=dict)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'customer_name': self.customer_name,
            'se_name':       self.se_name,
            'started_at':    self.started_at.strftime('%Y-%m-%d %H:%M') if self.started_at else '',
            'completed_at':  self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else '',
            'answers':       self.answers or {},
            'results':       self.results or {},
            'created_at':    self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
        }


# ─────────────────────────────────────────
# MIGRATION HELPER
# ─────────────────────────────────────────
def run_migration(db):
    import sqlalchemy as sa
    engine    = db.engine
    inspector = sa.inspect(engine)
    existing  = inspector.get_table_names()
    new_tables = ['option_assets','option_valueprops','option_testcases',
                  'option_povsteps','option_roadblocks']
    for tname in new_tables:
        if tname not in existing:
            db.metadata.tables[tname].create(engine)
            print(f'[migration] Created table: {tname}')
    # Drop old single-FK columns if they exist
    with engine.connect() as conn:
        cols     = [c['name'] for c in inspector.get_columns('question_options')]
        old_cols = ['asset_id','value_prop_id','test_case_id','pov_step_id','roadblock_id']
        for col in old_cols:
            if col in cols:
                try:
                    conn.execute(sa.text(f'ALTER TABLE question_options DROP COLUMN {col}'))
                    print(f'[migration] Dropped column question_options.{col}')
                except Exception as e:
                    print(f'[migration] Could not drop {col}: {e}')
        conn.commit()
