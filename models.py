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

class QuestionVisibilityRule(db.Model):
    __tablename__ = 'question_visibility_rules'
    id                 = db.Column(db.Integer, primary_key=True)
    parent_question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    option_id          = db.Column(db.Integer, db.ForeignKey('question_options.id', ondelete='CASCADE'), nullable=False)
    child_question_id  = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    created_at         = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('parent_question_id', 'option_id', 'child_question_id', name='uq_vis_rule'),
    )

    parent_question = db.relationship('Question', foreign_keys=[parent_question_id],
                                       backref=db.backref('visibility_rules_as_parent', cascade='all, delete-orphan', lazy=True))
    child_question  = db.relationship('Question', foreign_keys=[child_question_id],
                                       backref=db.backref('visibility_rules_as_child', cascade='all, delete-orphan', lazy=True))
    option          = db.relationship('QuestionOption', foreign_keys=[option_id], lazy=True)

    def to_dict(self):
        return {
            'id':                 self.id,
            'parent_question_id': self.parent_question_id,
            'option_id':          self.option_id,
            'child_question_id':  self.child_question_id,
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
    pricing_data           = db.Column(db.JSON, default=dict)
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
            'pricing_data':           self.pricing_data or {},
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

class BVAConfig(db.Model):
    __tablename__ = 'bva_config'
    id                 = db.Column(db.Integer, primary_key=True)
    site_count_keyword = db.Column(db.String(100), default='no_of_sites')
    device_count       = db.Column(db.Float, default=345)
    hw_cost            = db.Column(db.Float, default=3500)
    hw_support_pct     = db.Column(db.Float, default=20)
    mpls_cost          = db.Column(db.Float, default=1200)
    broadband_cost     = db.Column(db.Float, default=350)
    mpls_usage_pct     = db.Column(db.Float, default=90)
    fte_count          = db.Column(db.Float, default=6)
    fte_salary         = db.Column(db.Float, default=125000)
    fte_time_pct       = db.Column(db.Float, default=45)
    breach_cost        = db.Column(db.Float, default=2500000)
    legacy_risk_pct    = db.Column(db.Float, default=18)
    zscaler_risk_pct   = db.Column(db.Float, default=1.5)
    updated_at         = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':                 self.id,
            'site_count_keyword': self.site_count_keyword,
            'device_count':       self.device_count,
            'hw_cost':            self.hw_cost,
            'hw_support_pct':     self.hw_support_pct,
            'mpls_cost':          self.mpls_cost,
            'broadband_cost':     self.broadband_cost,
            'mpls_usage_pct':     self.mpls_usage_pct,
            'fte_count':          self.fte_count,
            'fte_salary':         self.fte_salary,
            'fte_time_pct':       self.fte_time_pct,
            'breach_cost':        self.breach_cost,
            'legacy_risk_pct':    self.legacy_risk_pct,
            'zscaler_risk_pct':   self.zscaler_risk_pct,
        }

class BVASection(db.Model):
    __tablename__ = 'bva_sections'
    id          = db.Column(db.Integer, primary_key=True)
    key         = db.Column(db.String(100), nullable=False, unique=True)
    label       = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default='')
    color       = db.Column(db.String(20), default='#6366f1')
    formula     = db.Column(db.Text, nullable=False)
    order       = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'key':         self.key,
            'label':       self.label,
            'description': self.description,
            'color':       self.color,
            'formula':     self.formula,
            'order':       self.order,
        }

class PricingSKU(db.Model):
    __tablename__ = 'pricing_skus'
    id            = db.Column(db.Integer, primary_key=True)
    sku_code      = db.Column(db.String(100), nullable=False)
    sku_name      = db.Column(db.String(255), nullable=False)
    category      = db.Column(db.String(50), nullable=False)
    cogs          = db.Column(db.Float, default=0)
    list_price    = db.Column(db.Float, default=0)
    budgetary     = db.Column(db.Float, default=0)
    standard      = db.Column(db.Float, default=0)
    aggressive    = db.Column(db.Float, default=0)
    is_ha         = db.Column(db.Boolean, default=False)
    ha_parent_id  = db.Column(db.Integer, db.ForeignKey('pricing_skus.id', ondelete='SET NULL'), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    active        = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ha_parent     = db.relationship('PricingSKU', remote_side='PricingSKU.id',
                                     foreign_keys='PricingSKU.ha_parent_id', lazy=True)

    def to_dict(self):
        return {
            'id':            self.id,
            'sku_code':      self.sku_code,
            'sku_name':      self.sku_name,
            'category':      self.category,
            'cogs':          self.cogs,
            'list_price':    self.list_price,
            'budgetary':     self.budgetary,
            'standard':      self.standard,
            'aggressive':    self.aggressive,
            'is_ha':         self.is_ha,
            'ha_parent_id':  self.ha_parent_id,
            'display_order': self.display_order,
            'active':        self.active,
        }

# ── NEW: TCO Entry ─────────────────────────────────────────────────────────────
# Stores per-category vendor/size pricing for the TCO Analysis tab.
# category values: fw_ns | sdwan | mpls | fw_ew | iot_ot | nac | l3sw | pam
class TCOEntry(db.Model):
    __tablename__ = 'tco_entries'
    id            = db.Column(db.Integer, primary_key=True)
    category      = db.Column(db.String(30), nullable=False)   # e.g. 'fw_ns'
    vendor        = db.Column(db.String(150), nullable=False)
    size          = db.Column(db.String(20), nullable=False)   # Small/Medium/Large/XL
    sku_name      = db.Column(db.String(255), nullable=False)  # display label in dropdown
    annual_cost   = db.Column(db.Float, nullable=False, default=0)  # $ per site per year
    display_order = db.Column(db.Integer, default=0)
    active        = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id':            self.id,
            'category':      self.category,
            'vendor':        self.vendor,
            'size':          self.size,
            'sku_name':      self.sku_name,
            'annual_cost':   self.annual_cost,
            'display_order': self.display_order,
            'active':        self.active,
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

    if 'question_visibility_rules' not in existing:
        db.metadata.tables['question_visibility_rules'].create(engine)
        print('[migration] Created table: question_visibility_rules')

    if 'bva_config' not in existing:
        db.metadata.tables['bva_config'].create(engine)
        print('[migration] Created table: bva_config')
        with engine.connect() as c:
            c.execute(sa.text("""
                INSERT INTO bva_config (
                    id, site_count_keyword, device_count, hw_cost, hw_support_pct,
                    mpls_cost, broadband_cost, mpls_usage_pct,
                    fte_count, fte_salary, fte_time_pct,
                    breach_cost, legacy_risk_pct, zscaler_risk_pct
                ) VALUES (
                    1, 'no_of_sites', 345, 3500, 20,
                    1200, 350, 90,
                    6, 125000, 45,
                    2500000, 18, 1.5
                )
            """))
            c.commit()
        print('[migration] Seeded default BVAConfig row')

    if 'bva_sections' not in existing:
        db.metadata.tables['bva_sections'].create(engine)
        print('[migration] Created table: bva_sections')
        with engine.connect() as c:
            c.execute(sa.text("""
                INSERT INTO bva_sections (key, label, description, color, formula, "order") VALUES
                ('infra_reduction', 'Infrastructure Reduction',     'No local WAN firewalls or VPN concentrators.',         '#6366f1', 'legacyHwCost * 0.75',           1),
                ('network_savings', 'Networking Transform Savings', 'Expensive MPLS circuits converted to local broadband.','#22c55e', 'legacyNetwork - zscalerNetwork', 2),
                ('fte_liberation',  'FTE Hours Liberated',          'Securing rule setups and troubleshooting logs.',        '#eab308', 'fteCost * fteSavingsFactor',     3)
            """))
            c.commit()
        print('[migration] Seeded default BVASections')

    # ── Pricing SKUs ──────────────────────────────────────────────────────────
    if 'pricing_skus' not in existing:
        db.metadata.tables['pricing_skus'].create(engine)
        print('[migration] Created table: pricing_skus')
        with engine.connect() as c:
            c.execute(sa.text("""
                INSERT INTO pricing_skus
                    (sku_code, sku_name, category, cogs, list_price, budgetary, standard, aggressive, is_ha, ha_parent_id, display_order, active)
                VALUES
                ('ZTB-400',        'ZTB-400 (No HA)',        'appliance',   914,   1200,   600,   450,   383,  false, NULL, 1,  true),
                ('ZTB-600',        'ZTB-600 (No HA)',        'appliance',   760,   1800,   900,   675,   574,  false, NULL, 2,  true),
                ('ZTB-800',        'ZTB-800 (No HA)',        'appliance',  2100,   3600,  1800,  1350,  1148,  false, NULL, 3,  true),
                ('ZTB-8010',       'ZTB-8010 (No HA)',       'appliance',  6134,  18000,  9000,  6750,  5738,  false, NULL, 4,  true),
                ('ZTB-400-HA',     'ZTB-400 (Include HA)',   'appliance',  1828,   2400,  1200,   900,   766,  true,  NULL, 5,  true),
                ('ZTB-600-HA',     'ZTB-600 (Include HA)',   'appliance',  1520,   3600,  1800,  1350,  1148,  true,  NULL, 6,  true),
                ('ZTB-800-HA',     'ZTB-800 (Include HA)',   'appliance',  4200,   7200,  3600,  2700,  2296,  true,  NULL, 7,  true),
                ('ZTB-8010-HA',    'ZTB-8010 (Include HA)',  'appliance', 12268,  36000, 18000, 13500, 11476,  true,  NULL, 8,  true),
                ('ZTB-SDWAN-SMALL','ZTB-SDWAN-SMALL',        'sdwan',         0,   2400,  1000,   750,   500,  false, NULL, 9,  true),
                ('ZTB-SDWAN-MED',  'ZTB-SDWAN-MED',          'sdwan',         0,   4800,  2000,  1500,  1000,  false, NULL, 10, true),
                ('ZTB-SDWAN-LARGE','ZTB-SDWAN-LARGE',         'sdwan',         0,  12000,  5000,  3750,  2500,  false, NULL, 11, true),
                ('ZTB-SDWAN-XL',   'ZTB-SDWAN-XL',           'sdwan',         0,  30000, 12500,  9375,  6250,  false, NULL, 12, true),
                ('ZTB-SG-SMALL',   'ZTB-SG-SMALL',           'segmentation',  0,   4800,  2000,  1500,  1000,  false, NULL, 13, true),
                ('ZTB-SG-MED',     'ZTB-SG-MED',             'segmentation',  0,  18000,  7500,  5625,  3750,  false, NULL, 14, true),
                ('ZTB-SG-LARGE',   'ZTB-SG-LARGE',           'segmentation',  0,  48000, 20000, 15000, 10000,  false, NULL, 15, true),
                ('ZTB-SG-XL',      'ZTB-SG-XL',              'segmentation',  0, 120000, 50000, 37500, 25000,  false, NULL, 16, true)
            """))
            c.commit()
            c.execute(sa.text("""
                UPDATE pricing_skus ha
                SET ha_parent_id = noha.id
                FROM pricing_skus noha
                WHERE ha.sku_code = noha.sku_code || '-HA'
                  AND ha.is_ha = true
            """))
            c.commit()
        print('[migration] Seeded 16 pricing SKUs')

    # ── TCO Entries ───────────────────────────────────────────────────────────
    if 'tco_entries' not in existing:
        db.metadata.tables['tco_entries'].create(engine)
        print('[migration] Created table: tco_entries')
        with engine.connect() as c:
            c.execute(sa.text("""
                INSERT INTO tco_entries (category, vendor, size, sku_name, annual_cost, display_order, active) VALUES
                -- FW N/S
                ('fw_ns','Palo Alto Networks','Small', 'PA-460 Small',          683,  1, true),
                ('fw_ns','Palo Alto Networks','Medium','PA-1410 Medium',        1900, 2, true),
                ('fw_ns','Palo Alto Networks','Large', 'PA-3420 Large',         8759, 3, true),
                ('fw_ns','Palo Alto Networks','XL',    'PA-5440 XL',           47653, 4, true),
                ('fw_ns','Fortinet','Small',  'FortiGate 80F Small',            268,  5, true),
                ('fw_ns','Fortinet','Medium', 'FortiGate 200F Medium',          947,  6, true),
                ('fw_ns','Fortinet','Large',  'FortiGate 600E Large',          2276,  7, true),
                ('fw_ns','Fortinet','XL',     'FortiGate 3400E XL',            7227,  8, true),
                ('fw_ns','Cisco','Small',     'Cisco FTD 1010 Small',           450,  9, true),
                ('fw_ns','Cisco','Medium',    'Cisco FTD 2110 Medium',         1200, 10, true),
                ('fw_ns','Cisco','Large',     'Cisco FTD 4115 Large',          5400, 11, true),
                ('fw_ns','Cisco','XL',        'Cisco FTD 4145 XL',            18000, 12, true),
                ('fw_ns','Check Point','Small', 'CP 1570 Small',               380, 13, true),
                ('fw_ns','Check Point','Medium','CP 6200 Medium',             1100, 14, true),
                ('fw_ns','Check Point','Large', 'CP 16200 Large',             4200, 15, true),
                ('fw_ns','Check Point','XL',    'CP 26000 XL',               14000, 16, true),
                -- SD-WAN
                ('sdwan','Fortinet Secure SD-WAN','Small', 'FortiGate SD-WAN Small',   220, 17, true),
                ('sdwan','Fortinet Secure SD-WAN','Medium','FortiGate SD-WAN Medium',  780, 18, true),
                ('sdwan','Fortinet Secure SD-WAN','Large', 'FortiGate SD-WAN Large',  2100, 19, true),
                ('sdwan','Fortinet Secure SD-WAN','XL',    'FortiGate SD-WAN XL',     5600, 20, true),
                ('sdwan','Cisco Meraki','Small', 'MX68 SD-WAN Small',                 237, 21, true),
                ('sdwan','Cisco Meraki','Medium','MX250 SD-WAN Medium',             2050, 22, true),
                ('sdwan','Cisco Meraki','Large', 'MX450 SD-WAN Large',             3434, 23, true),
                ('sdwan','Cisco Meraki','XL',    'MX600 SD-WAN XL',               6868, 24, true),
                ('sdwan','VMware VeloCloud','Small', 'VeloCloud 510 Small',          195, 25, true),
                ('sdwan','VMware VeloCloud','Medium','VeloCloud 540 Medium',         680, 26, true),
                ('sdwan','VMware VeloCloud','Large', 'VeloCloud 3400 Large',        1850, 27, true),
                ('sdwan','VMware VeloCloud','XL',    'VeloCloud 3800 XL',          4900, 28, true),
                ('sdwan','Palo Alto Prisma SD-WAN','Small', 'Prisma SD-WAN 3200 Small',  310, 29, true),
                ('sdwan','Palo Alto Prisma SD-WAN','Medium','Prisma SD-WAN 5200 Medium', 960, 30, true),
                ('sdwan','Palo Alto Prisma SD-WAN','Large', 'Prisma SD-WAN 7200 Large', 2600, 31, true),
                ('sdwan','Palo Alto Prisma SD-WAN','XL',    'Prisma SD-WAN 7200 XL',   6900, 32, true),
                -- MPLS
                ('mpls','AT&T','Small', 'AT&T AVPN Small',    9600,  33, true),
                ('mpls','AT&T','Medium','AT&T AVPN Medium',   16200, 34, true),
                ('mpls','AT&T','Large', 'AT&T AVPN Large',    21000, 35, true),
                ('mpls','AT&T','XL',    'AT&T AVPN XL',      138000, 36, true),
                ('mpls','Verizon','Small', 'Verizon Private IP Small',   8400,  37, true),
                ('mpls','Verizon','Medium','Verizon Private IP Medium',  14400, 38, true),
                ('mpls','Verizon','Large', 'Verizon Private IP Large',   19200, 39, true),
                ('mpls','Verizon','XL',    'Verizon Private IP XL',     120000, 40, true),
                ('mpls','Lumen','Small', 'Lumen IP VPN Small',   7200,  41, true),
                ('mpls','Lumen','Medium','Lumen IP VPN Medium',  12000, 42, true),
                ('mpls','Lumen','Large', 'Lumen IP VPN Large',   16800, 43, true),
                ('mpls','Lumen','XL',    'Lumen IP VPN XL',     108000, 44, true),
                -- FW E/W (Micro-Seg)
                ('fw_ew','Illumio','Small', 'Illumio Core Small',      1800, 45, true),
                ('fw_ew','Illumio','Medium','Illumio Core Medium',      7200, 46, true),
                ('fw_ew','Illumio','Large', 'Illumio Core Large',      36000, 47, true),
                ('fw_ew','Illumio','XL',    'Illumio Core XL',        144000, 48, true),
                ('fw_ew','Akamai Guardicore','Small', 'Guardicore Small',   2100, 49, true),
                ('fw_ew','Akamai Guardicore','Medium','Guardicore Medium',  8400, 50, true),
                ('fw_ew','Akamai Guardicore','Large', 'Guardicore Large',  42000, 51, true),
                ('fw_ew','Akamai Guardicore','XL',    'Guardicore XL',    168000, 52, true),
                ('fw_ew','Broadcom vDefend','Small', 'VMware NSX Small',    2592, 53, true),
                ('fw_ew','Broadcom vDefend','Medium','VMware NSX Medium',  11520, 54, true),
                ('fw_ew','Broadcom vDefend','Large', 'VMware NSX Large',   96000, 55, true),
                ('fw_ew','Broadcom vDefend','XL',    'VMware NSX XL',     384000, 56, true),
                -- IoT/OT
                ('iot_ot','Claroty xDome','Small', 'Claroty xDome Small',     1200, 57, true),
                ('iot_ot','Claroty xDome','Medium','Claroty xDome Medium',    4800, 58, true),
                ('iot_ot','Claroty xDome','Large', 'Claroty xDome Large',    24000, 59, true),
                ('iot_ot','Claroty xDome','XL',    'Claroty xDome XL',      113400, 60, true),
                ('iot_ot','Armis Centrix','Small', 'Armis Centrix Small',    1440, 61, true),
                ('iot_ot','Armis Centrix','Medium','Armis Centrix Medium',   5760, 62, true),
                ('iot_ot','Armis Centrix','Large', 'Armis Centrix Large',   28800, 63, true),
                ('iot_ot','Armis Centrix','XL',    'Armis Centrix XL',     136080, 64, true),
                ('iot_ot','Forescout','Small', 'Forescout eyeInspect Small',   2213, 65, true),
                ('iot_ot','Forescout','Medium','Forescout eyeInspect Medium',  8850, 66, true),
                ('iot_ot','Forescout','Large', 'Forescout eyeInspect Large',  44250, 67, true),
                ('iot_ot','Forescout','XL',    'Forescout eyeInspect XL',   209250, 68, true),
                -- NAC
                ('nac','Cisco ISE','Small', 'Cisco ISE Small',      5339, 69, true),
                ('nac','Cisco ISE','Medium','Cisco ISE Medium',     12141, 70, true),
                ('nac','Cisco ISE','Large', 'Cisco ISE Large',      31647, 71, true),
                ('nac','Cisco ISE','XL',    'Cisco ISE XL',         63294, 72, true),
                ('nac','HPE Aruba ClearPass','Small', 'ClearPass Small',   3600, 73, true),
                ('nac','HPE Aruba ClearPass','Medium','ClearPass Medium',  8640, 74, true),
                ('nac','HPE Aruba ClearPass','Large', 'ClearPass Large',  21600, 75, true),
                ('nac','HPE Aruba ClearPass','XL',    'ClearPass XL',     43200, 76, true),
                ('nac','Fortinet FortiNAC','Small', 'FortiNAC Small',   2400, 77, true),
                ('nac','Fortinet FortiNAC','Medium','FortiNAC Medium',  5760, 78, true),
                ('nac','Fortinet FortiNAC','Large', 'FortiNAC Large',  14400, 79, true),
                ('nac','Fortinet FortiNAC','XL',    'FortiNAC XL',    28800, 80, true),
                -- L3 Switching
                ('l3sw','Cisco Catalyst 9000','Small', 'Catalyst 9200 Small',   851,  81, true),
                ('l3sw','Cisco Catalyst 9000','Medium','Catalyst 9300 Medium',  2906, 82, true),
                ('l3sw','Cisco Catalyst 9000','Large', 'Catalyst 9400 Large',  13428, 83, true),
                ('l3sw','Cisco Catalyst 9000','XL',    'Catalyst 9600 XL',    12263, 84, true),
                ('l3sw','Cisco Meraki MS','Small', 'Meraki MS120 Small',   960,  85, true),
                ('l3sw','Cisco Meraki MS','Medium','Meraki MS250 Medium', 3240, 86, true),
                ('l3sw','Cisco Meraki MS','Large', 'Meraki MS410 Large', 15000, 87, true),
                ('l3sw','Cisco Meraki MS','XL',    'Meraki MS425 XL',   13800, 88, true),
                ('l3sw','HPE Aruba CX','Small', 'Aruba CX 6200 Small',   720,  89, true),
                ('l3sw','HPE Aruba CX','Medium','Aruba CX 6300 Medium', 2400, 90, true),
                ('l3sw','HPE Aruba CX','Large', 'Aruba CX 8360 Large', 10800, 91, true),
                ('l3sw','HPE Aruba CX','XL',    'Aruba CX 10000 XL',   9600, 92, true),
                -- PAM
                ('pam','CyberArk Privilege Cloud','Small', 'CyberArk PAM Small',    13410, 93, true),
                ('pam','CyberArk Privilege Cloud','Medium','CyberArk PAM Medium',   72000, 94, true),
                ('pam','CyberArk Privilege Cloud','Large', 'CyberArk PAM Large',   210000, 95, true),
                ('pam','CyberArk Privilege Cloud','XL',    'CyberArk PAM XL',      660000, 96, true),
                ('pam','BeyondTrust PRA','Small', 'BeyondTrust PRA Small',   9600,  97, true),
                ('pam','BeyondTrust PRA','Medium','BeyondTrust PRA Medium',  48000, 98, true),
                ('pam','BeyondTrust PRA','Large', 'BeyondTrust PRA Large',  144000, 99, true),
                ('pam','BeyondTrust PRA','XL',    'BeyondTrust PRA XL',     480000, 100, true),
                ('pam','Delinea Secret Server','Small', 'Delinea SS Small',    7200,  101, true),
                ('pam','Delinea Secret Server','Medium','Delinea SS Medium',   36000, 102, true),
                ('pam','Delinea Secret Server','Large', 'Delinea SS Large',   108000, 103, true),
                ('pam','Delinea Secret Server','XL',    'Delinea SS XL',      360000, 104, true)
            """))
            c.commit()
        print('[migration] Seeded TCO entries (104 rows across 8 categories)')

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
        if 'pricing_data' not in ur_cols:
            conn.execute(sa.text(
                'ALTER TABLE user_responses ADD COLUMN pricing_data JSON'
            ))
            print('[migration] Added column user_responses.pricing_data')

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
