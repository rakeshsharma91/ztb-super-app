# admin_questions_routes.py
from flask import Blueprint, request, jsonify, session
from models import (db, Question, QuestionCategory, QuestionOption,
                    Asset, ValueProp, TestCase, POVPlanner, Roadblock)
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

def opt_to_dict(o):
    return {
        'id':            o.id,
        'question_id':   o.question_id,
        'option_text':   o.label,
        'asset_ids':     [a.id for a in o.assets],
        'valueprop_ids': [v.id for v in o.value_props],
        'testcase_ids':  [t.id for t in o.test_cases],
        'povstep_ids':   [p.id for p in o.pov_steps],
        'roadblock_ids': [r.id for r in o.roadblocks],
    }

def q_to_dict(q):
    return {
        'id':            q.id,
        'question_text': q.text,
        'keyword':       q.category_ref.name if q.category_ref else '',
        'category_id':   q.category_id,
        'options_type':  q.options_type or 'Select One',
        'info_only':     q.info_only,
        'order':         q.order,
        'options':       [opt_to_dict(o) for o in sorted(q.options, key=lambda o: o.id)],
    }

def get_or_create_category(name):
    name = (name or 'General').strip() or 'General'
    cat = QuestionCategory.query.filter_by(name=name).first()
    if not cat:
        cat = QuestionCategory(name=name, order=0)
        db.session.add(cat)
        db.session.flush()
    return cat

def _sync_m2m(opt, field, ids, model):
    ids  = [int(i) for i in (ids or []) if i]
    objs = model.query.filter(model.id.in_(ids)).all() if ids else []
    setattr(opt, field, objs)

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

# ── POST /admin/questions/reorder ─────────────────────────────────────────────
@admin_questions_bp.route('/reorder', methods=['POST'])
@require_admin
def reorder_questions():
    data  = request.get_json() or {}
    items = data.get('order', [])
    for item in items:
        q = Question.query.get(item.get('id'))
        if q:
            q.order = int(item.get('order', 0))
    db.session.commit()
    return jsonify({'message': 'reordered'}), 200

# ── PATCH /admin/questions/<id> ───────────────────────────────────────────────
@admin_questions_bp.route('/<int:qid>', methods=['PATCH'])
@require_admin
def patch_question(qid):
    q     = Question.query.get_or_404(qid)
    data  = request.get_json() or {}
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
        question_id = qid,
        label       = data.get('option_text') or data.get('label') or '',
    )
    db.session.add(opt)
    db.session.flush()
    _sync_m2m(opt, 'assets',      data.get('asset_ids'),     Asset)
    _sync_m2m(opt, 'value_props', data.get('valueprop_ids'), ValueProp)
    _sync_m2m(opt, 'test_cases',  data.get('testcase_ids'),  TestCase)
    _sync_m2m(opt, 'pov_steps',   data.get('povstep_ids'),   POVPlanner)
    _sync_m2m(opt, 'roadblocks',  data.get('roadblock_ids'), Roadblock)
    db.session.commit()
    return jsonify(opt_to_dict(opt)), 201

# ── PATCH /admin/questions/<id>/options/<oid> ─────────────────────────────────
@admin_questions_bp.route('/<int:qid>/options/<int:oid>', methods=['PATCH'])
@require_admin
def patch_option(qid, oid):
    opt   = QuestionOption.query.filter_by(id=oid, question_id=qid).first_or_404()
    data  = request.get_json() or {}
    field = data.get('field')
    value = data.get('value')

    if field in ('option_text', 'label'):
        opt.label = value or ''
    elif field == 'asset_ids':
        _sync_m2m(opt, 'assets',      value, Asset)
    elif field == 'valueprop_ids':
        _sync_m2m(opt, 'value_props', value, ValueProp)
    elif field == 'testcase_ids':
        _sync_m2m(opt, 'test_cases',  value, TestCase)
    elif field == 'povstep_ids':
        _sync_m2m(opt, 'pov_steps',   value, POVPlanner)
    elif field == 'roadblock_ids':
        _sync_m2m(opt, 'roadblocks',  value, Roadblock)

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
