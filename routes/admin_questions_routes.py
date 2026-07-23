# admin_questions_routes.py
from flask import Blueprint, request, jsonify, session
from models import db, Question, QuestionCategory, QuestionOption
from functools import wraps
from datetime import datetime

admin_questions_bp = Blueprint('admin_questions', __name__, url_prefix='/admin/questions')

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def q_to_dict(q):
    """Serialize Question using field names the HTML frontend expects."""
    return {
        'id':           q.id,
        'question_text': q.text,
        'keyword':      q.category_ref.name if q.category_ref else '',
        'category_id':  q.category_id,
        'options_type': q.options_type or 'Select One',
        'info_only':    q.info_only,
        'order':        q.order,
        'options': [opt_to_dict(o) for o in
                    sorted(q.options, key=lambda o: o.id)]
    }

def opt_to_dict(o):
    return {
        'id':           o.id,
        'question_id':  o.question_id,
        'option_text':  o.label,
        'asset_id':     o.asset_id,
        'valueprop_id': o.value_prop_id,
        'testcase_id':  o.test_case_id,
        'povstep_id':   o.pov_step_id,
        'roadblock_id': o.roadblock_id,
    }

def get_or_create_category(name):
    name = (name or 'General').strip() or 'General'
    cat = QuestionCategory.query.filter_by(name=name).first()
    if not cat:
        cat = QuestionCategory(name=name, order=0)
        db.session.add(cat)
        db.session.flush()
    return cat

# ── GET /admin/questions/ ─────────────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['GET'])
@require_admin
def list_questions():
    qs = Question.query.order_by(Question.category_id, Question.order, Question.id).all()
    return jsonify([q_to_dict(q) for q in qs]), 200

# ── POST /admin/questions/ ────────────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['POST'])
@require_admin
def create_question():
    data = request.get_json() or {}
    cat  = get_or_create_category(data.get('keyword') or data.get('category') or 'General')
    q = Question(
        text         = (data.get('question_text') or '').strip() or 'New Question',
        category_id  = cat.id,
        options_type = data.get('options_type', 'Select One'),
        info_only    = bool(data.get('info_only', False)),
        order        = int(data.get('order', 0)),
    )
    db.session.add(q)
    db.session.commit()
    return jsonify(q_to_dict(q)), 201

# ── PATCH /admin/questions/<id> ───────────────────────────────────────────────
@admin_questions_bp.route('/<int:qid>', methods=['PATCH'])
@require_admin
def patch_question(qid):
    q    = Question.query.get_or_404(qid)
    data = request.get_json() or {}
    field = data.get('field')
    value = data.get('value', '')

    if field == 'question_text':
        q.text = value
    elif field == 'keyword':
        cat = get_or_create_category(value)
        q.category_id = cat.id
    elif field == 'options_type':
        q.options_type = value
    elif field == 'info_only':
        q.info_only = bool(value)
    elif field == 'order':
        try: q.order = int(value)
        except: pass
    # additional_details has no DB column — silently ignore

    q.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(q_to_dict(q)), 200

# ── DELETE /admin/questions/<id> ──────────────────────────────────────────────
@admin_questions_bp.route('/<int:qid>', methods=['DELETE'])
@require_admin
def delete_question(qid):
    q = Question.query.get_or_404(qid)
    db.session.delete(q)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200

# ── POST /admin/questions/<id>/options ────────────────────────────────────────
@admin_questions_bp.route('/<int:qid>/options', methods=['POST'])
@require_admin
def add_option(qid):
    Question.query.get_or_404(qid)
    data = request.get_json() or {}
    opt  = QuestionOption(
        question_id   = qid,
        label         = data.get('option_text') or data.get('label') or '',
        value_prop_id = data.get('valueprop_id') or data.get('value_prop_id'),
        asset_id      = data.get('asset_id'),
        test_case_id  = data.get('testcase_id') or data.get('test_case_id'),
        pov_step_id   = data.get('povstep_id')  or data.get('pov_step_id'),
        roadblock_id  = data.get('roadblock_id'),
    )
    db.session.add(opt)
    db.session.commit()
    return jsonify(opt_to_dict(opt)), 201

# ── PATCH /admin/questions/<id>/options/<oid> ─────────────────────────────────
@admin_questions_bp.route('/<int:qid>/options/<int:oid>', methods=['PATCH'])
@require_admin
def patch_option(qid, oid):
    opt  = QuestionOption.query.filter_by(id=oid, question_id=qid).first_or_404()
    data = request.get_json() or {}
    field = data.get('field')
    value = data.get('value') or None

    mapping = {
        'option_text':  'label',
        'label':        'label',
        'asset_id':     'asset_id',
        'valueprop_id': 'value_prop_id',
        'testcase_id':  'test_case_id',
        'povstep_id':   'pov_step_id',
        'roadblock_id': 'roadblock_id',
        'action':       None,   # no DB column, ignore
    }
    db_field = mapping.get(field)
    if db_field:
        setattr(opt, db_field, value)

    db.session.commit()
    return jsonify(opt_to_dict(opt)), 200

# ── DELETE /admin/questions/<id>/options/<oid> ────────────────────────────────
@admin_questions_bp.route('/<int:qid>/options/<int:oid>', methods=['DELETE'])
@require_admin
def delete_option(qid, oid):
    opt = QuestionOption.query.filter_by(id=oid, question_id=qid).first_or_404()
    db.session.delete(opt)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200

# ── GET /admin/questions/categories ──────────────────────────────────────────
@admin_questions_bp.route('/categories', methods=['GET'])
@require_admin
def list_categories():
    cats = QuestionCategory.query.order_by(QuestionCategory.order,
                                           QuestionCategory.name).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in cats]), 200
