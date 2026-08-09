# admin_questions_routes.py
from flask import Blueprint, request, jsonify, session
from models import (db, Question, QuestionCategory, QuestionOption,
                    QuestionCategoryType, QuestionVisibilityRule,
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
        'id':                  q.id,
        'question_text':       q.text,
        'keyword':             q.category_ref.name if q.category_ref else '',
        'category_id':         q.category_id,
        'category_type_id':    q.category_type_id,
        'category_type_name':  q.category_type_ref.name if q.category_type_ref else '',
        'options_type':        q.options_type or 'Select One',
        'info_only':           q.info_only,
        'hidden':              q.hidden,
        'default_option_id':   q.default_option_id,
        'order':               q.order,
        'options':             [opt_to_dict(o) for o in sorted(q.options, key=lambda o: o.id)],
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

# ── GET /admin/questions/category-types ──────────────────────────────────────
@admin_questions_bp.route('/category-types', methods=['GET'])
@require_admin
def list_category_types():
    types = QuestionCategoryType.query.order_by(QuestionCategoryType.name).all()
    return jsonify([{'id': t.id, 'name': t.name} for t in types]), 200

# ── POST /admin/questions/category-types ─────────────────────────────────────
@admin_questions_bp.route('/category-types', methods=['POST'])
@require_admin
def create_category_type():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    existing = QuestionCategoryType.query.filter_by(name=name).first()
    if existing:
        return jsonify({'id': existing.id, 'name': existing.name}), 200
    ct = QuestionCategoryType(name=name)
    db.session.add(ct)
    db.session.commit()
    return jsonify({'id': ct.id, 'name': ct.name}), 201

# ── GET /admin/questions/ ─────────────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['GET'])
@require_admin
def list_questions():
    qs = Question.query.order_by(Question.order, Question.id).all()
    return jsonify([q_to_dict(q) for q in qs]), 200

# ── POST /admin/questions/ ────────────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['POST'])
@require_admin
def create_question():
    data = request.get_json() or {}
    cat  = get_or_create_category(data.get('keyword') or data.get('category') or 'General')
    max_order = db.session.query(db.func.max(Question.order)).scalar() or 0
    q = Question(
        text              = (data.get('question_text') or '').strip() or 'New Question',
        category_id       = cat.id,
        category_type_id  = data.get('category_type_id') or None,
        options_type      = data.get('options_type', 'Select One'),
        info_only         = bool(data.get('info_only', False)),
        hidden            = bool(data.get('hidden', False)),
        default_option_id = data.get('default_option_id') or None,
        order             = max_order + 1,
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
    elif field == 'hidden':
        q.hidden = bool(value)
        if not bool(value):
            q.default_option_id = None
    elif field == 'default_option_id':
        if value is None or value == '' or value == 0:
            q.default_option_id = None
        else:
            try:
                opt_id = int(value)
                opt = QuestionOption.query.filter_by(id=opt_id, question_id=qid).first()
                q.default_option_id = opt.id if opt else None
            except (ValueError, TypeError):
                q.default_option_id = None
    elif field == 'order':
        try: q.order = int(value)
        except: pass
    elif field == 'category_type_id':
        if value is None or value == '':
            q.category_type_id = None
        elif isinstance(value, int) or (isinstance(value, str) and str(value).isdigit()):
            q.category_type_id = int(value)
        else:
            name = str(value).strip()
            ct = QuestionCategoryType.query.filter_by(name=name).first()
            if not ct:
                ct = QuestionCategoryType(name=name)
                db.session.add(ct)
                db.session.flush()
            q.category_type_id = ct.id

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
    q = Question.query.get(qid)
    if q and q.default_option_id == oid:
        q.default_option_id = None
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

# ── GET /admin/questions/visibility-rules ────────────────────────────────────
@admin_questions_bp.route('/visibility-rules', methods=['GET'])
@require_admin
def list_visibility_rules():
    rules = QuestionVisibilityRule.query.all()
    return jsonify([r.to_dict() for r in rules]), 200

# ── POST /admin/questions/<id>/visibility-rules ───────────────────────────────
@admin_questions_bp.route('/<int:qid>/visibility-rules', methods=['POST'])
@require_admin
def add_visibility_rule(qid):
    Question.query.get_or_404(qid)
    data             = request.get_json() or {}
    option_id        = data.get('option_id')
    child_question_id = data.get('child_question_id')
    if not option_id or not child_question_id:
        return jsonify({'error': 'option_id and child_question_id required'}), 400
    # Validate option belongs to parent question
    opt = QuestionOption.query.filter_by(id=int(option_id), question_id=qid).first()
    if not opt:
        return jsonify({'error': 'option not found on this question'}), 400
    # Validate child question exists
    child = Question.query.get(int(child_question_id))
    if not child:
        return jsonify({'error': 'child question not found'}), 400
    # Upsert — silently ignore duplicate
    existing = QuestionVisibilityRule.query.filter_by(
        parent_question_id=qid,
        option_id=int(option_id),
        child_question_id=int(child_question_id)
    ).first()
    if existing:
        return jsonify(existing.to_dict()), 200
    rule = QuestionVisibilityRule(
        parent_question_id=qid,
        option_id=int(option_id),
        child_question_id=int(child_question_id)
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(rule.to_dict()), 201

# ── DELETE /admin/questions/visibility-rules/<rule_id> ───────────────────────
@admin_questions_bp.route('/visibility-rules/<int:rule_id>', methods=['DELETE'])
@require_admin
def delete_visibility_rule(rule_id):
    rule = QuestionVisibilityRule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200
