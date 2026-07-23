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
# QUESTION OPTIONS
# ─────────────────────────────────────────
class QuestionOption(db.Model):
    __tablename__ = 'question_options'
    id            = db.Column(db.Integer, primary_key=True)
    question_id   = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    label         = db.Column(db.String(255), nullable=False)
    value_prop_id = db.Column(db.Integer, db.ForeignKey('value_props.id'), nullable=True)
    asset_id      = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=True)
    test_case_id  = db.Column(db.Integer, db.ForeignKey('test_cases.id'), nullable=True)
    pov_step_id   = db.Column(db.Integer, db.ForeignKey('pov_planner.id'), nullable=True)
    roadblock_id  = db.Column(db.Integer, db.ForeignKey('roadblocks.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

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

    def to_dict(self):  # serialize to dict
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

