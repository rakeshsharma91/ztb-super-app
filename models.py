from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admins'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password      = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class AdminConfig(db.Model):
    __tablename__ = 'admin_config'
    id         = db.Column(db.Integer, primary_key=True)
    key        = db.Column(db.String(255), unique=True, nullable=False)
    value      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

class ValueProp(db.Model):
    __tablename__ = 'value_props'
    id             = db.Column(db.Integer, primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text)
    business_value = db.Column(db.String(100))
    mandatory      = db.Column(db.Boolean, default=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Asset(db.Model):
    __tablename__ = 'assets'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(255), nullable=False)
    asset_type  = db.Column(db.String(100))
    url         = db.Column(db.Text)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(255), nullable=False)
    description     = db.Column(db.Text)
    steps           = db.Column(db.Text)
    expected_result = db.Column(db.Text)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class POVPlanner(db.Model):
    __tablename__ = 'pov_planner'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    duration    = db.Column(db.Text)
    owner       = db.Column(db.Text)
    status      = db.Column(db.String(50), default='Pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

class QuestionCategoryType(db.Model):
    __tablename__ = 'question_category_types'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions  = db.relationship('Question', backref='category_type_ref', lazy=True)

class QuestionCategory(db.Model):
    __tablename__ = 'question_categories'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(255), nullable=False, unique=True)
    order      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions  = db.relationship('Question', backref='category_ref', lazy=True,
                                  cascade='all, delete-orphan')

class Question(db.Model):
    __tablename__ = 'questions'
    id                 = db.Column(db.Integer, primary_key=True)
    category_id        = db.Column(db.Integer, db.ForeignKey('question_categories.id'), nullable=False)
    category_type_id   = db.Column(db.Integer, db.ForeignKey('question_category_types.id'), nullable=True)
    text               = db.Column(db.Text, nullable=False)
    options_type       = db.Column(db.String(50), default='select_one')
    order              = db.Column(db.Integer, default=0)
    info_only          = db.Column(db.Boolean, default=False)
    hidden             = db.Column(db.Boolean, default=False)
    default_option_id  = db.Column(db.Integer, db.ForeignKey('question_options.id',
                                   use_alter=True, name='fk_question_default_option'),
                                   nullable=True)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    options            = db.relationship('QuestionOption',
                                          foreign_keys='QuestionOption.question_id',
                                          backref='question', lazy=True,
                                          cascade='all, delete-orphan')
    default_option     = db.relationship('QuestionOption',
                                          foreign_keys='Question.default_option_id',
                                          lazy=True, post_update=True)

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

class UserResponse(db.Model):
    __tablename__ = 'user_responses'
    id                     = db.Column(db.Integer, primary_key=True)
    customer_name          = db.Column(db.String(255), nullable=False)
    se_name                = db.Column(db.String(255), nullable=False)
    opportunity_url        = db.Column(db.Text, nullable=True)
    status                 = db.Column(db.String(20), default='in_progress', nullable=False)
    current_question_index = db.Column(db.Integer, default=0)
    raw_responses          = db.Column(db.JSON, default=dict)
    started_at             = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at           = db.Column(db.DateTime, nullable=True)
    answers                = db.Column(db.JSON, default=dict)
    results                = db.Column(db.JSON, default=dict)
    notes                  = db.Column(db.Text, nullable=True)
    created_at             = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':                     self.id,
            'customer_name':          self.customer_name,
            'se_name':                self.se_name,
            'opportunity_url':        self.opportunity_url or '',
            'status':                 self.status,
            'current_question_index': self.current_question_index or 0,
            'started_at':             self.started_at.strftime('%Y-%m-%d %H:%M') if self.started_at else '',
            'completed_at':           self.completed_at.strftime('%Y-%m-%d %H:%M') if self.completed_at else '',
            'answers':                self.answers or {},
            'results':                self.results or {},
            'notes':                  self.notes or '',
            'created_at':             self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
        }

class ResultSection(db.Model):
    __tablename__ = 'result_sections'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(255), nullable=False)
    order      = db.Column(db.Integer, default=0)
    rules_json = db.Column(db.JSON, default=list)
    format     = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'order':      self.order,
            'rules_json': self.rules_json or [],
            'format':     self.format,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

def run_migration(db):
    import sqlalchemy as sa
    engine    = db.engine
    inspector = sa.inspect(engine)
    existing  = inspector.get_table_names()

    new_tables = ['option_assets', 'option_valueprops', 'option_testcases',
                  'option_povsteps', 'option_roadblocks', 'question_category_types']
    for tname in new_tables:
        if tname not in existing:
            db.metadata.tables[tname].create(engine)
            print(f'[migration] Created table: {tname}')

    if 'result_sections' not in existing:
        db.metadata.tables['result_sections'].create(engine)
        print('[migration] Created table: result_sections')

    with engine.connect() as conn:
        q_cols = [c['name'] for c in inspector.get_columns('questions')]

        if 'category_type_id' not in q_cols:
            conn.execute(sa.text(
                'ALTER TABLE questions ADD COLUMN category_type_id INTEGER '
                'REFERENCES question_category_types(id) ON DELETE SET NULL'
            ))
            print('[migration] Added column questions.category_type_id')

        if 'hidden' not in q_cols:
            conn.execute(sa.text(
                'ALTER TABLE questions ADD COLUMN hidden BOOLEAN NOT NULL DEFAULT FALSE'
            ))
            print('[migration] Added column questions.hidden')

        if 'default_option_id' not in q_cols:
            conn.execute(sa.text(
                'ALTER TABLE questions ADD COLUMN default_option_id INTEGER '
                'REFERENCES question_options(id) ON DELETE SET NULL'
            ))
            print('[migration] Added column questions.default_option_id')

        ur_cols = [c['name'] for c in inspector.get_columns('user_responses')]
        if 'status' not in ur_cols:
            conn.execute(sa.text(
                "ALTER TABLE user_responses ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'in_progress'"
            ))
            print('[migration] Added column user_responses.status')
        if 'current_question_index' not in ur_cols:
            conn.execute(sa.text(
                'ALTER TABLE user_responses ADD COLUMN current_question_index INTEGER DEFAULT 0'
            ))
            print('[migration] Added column user_responses.current_question_index')
        if 'raw_responses' not in ur_cols:
            conn.execute(sa.text(
                'ALTER TABLE user_responses ADD COLUMN raw_responses JSON'
            ))
            print('[migration] Added column user_responses.raw_responses')
        if 'notes' not in ur_cols:
            conn.execute(sa.text(
                'ALTER TABLE user_responses ADD COLUMN notes TEXT'
            ))
            print('[migration] Added column user_responses.notes')

        if 'result_sections' in existing:
            rs_cols = [c['name'] for c in inspector.get_columns('result_sections')]
            if 'format' not in rs_cols:
                conn.execute(sa.text(
                    'ALTER TABLE result_sections ADD COLUMN format VARCHAR(50)'
                ))
                print('[migration] Added column result_sections.format')

        conn.execute(sa.text(
            "UPDATE user_responses SET status = 'completed' WHERE completed_at IS NOT NULL AND status = 'in_progress'"
        ))

        old_cols = ['asset_id', 'value_prop_id', 'test_case_id', 'pov_step_id', 'roadblock_id']
        opt_cols = [c['name'] for c in inspector.get_columns('question_options')]
        for col in old_cols:
            if col in opt_cols:
                try:
                    conn.execute(sa.text(f'ALTER TABLE question_options DROP COLUMN {col}'))
                    print(f'[migration] Dropped column question_options.{col}')
                except Exception as e:
                    print(f'[migration] Could not drop {col}: {e}')

        conn.commit()
