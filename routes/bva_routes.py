# routes/bva_routes.py
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models import db, BVAConfig, BVASection, UserResponse
from functools import wraps
import re

bva_bp      = Blueprint('bva',      __name__, url_prefix='/admin/bva')
bva_user_bp = Blueprint('bva_user', __name__, url_prefix='/user')

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def _make_slug(name):
    slug = (name or 'unknown').strip().lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or 'unknown'

def _get_or_create_config():
    cfg = BVAConfig.query.get(1)
    if not cfg:
        cfg = BVAConfig(id=1)
        db.session.add(cfg)
        db.session.commit()
    return cfg

# ── Admin page ────────────────────────────────────────────────────────────────

@bva_bp.route('/', methods=['GET'])
def bva_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login_page'))
    return render_template('bva.html')

# ── BVAConfig CRUD ────────────────────────────────────────────────────────────

@bva_bp.route('/api/config', methods=['GET'])
@require_admin
def get_config():
    cfg = _get_or_create_config()
    return jsonify({'success': True, 'config': cfg.to_dict()})

@bva_bp.route('/api/config', methods=['PUT'])
@require_admin
def update_config():
    cfg  = _get_or_create_config()
    data = request.get_json()
    fields = [
        'site_count_keyword', 'device_count', 'hw_cost', 'hw_support_pct',
        'mpls_cost', 'broadband_cost', 'mpls_usage_pct',
        'fte_count', 'fte_salary', 'fte_time_pct',
        'breach_cost', 'legacy_risk_pct', 'zscaler_risk_pct'
    ]
    for f in fields:
        if f in data:
            setattr(cfg, f, data[f])
    db.session.commit()
    return jsonify({'success': True, 'config': cfg.to_dict()})

# ── BVASection CRUD ───────────────────────────────────────────────────────────

@bva_bp.route('/api/sections', methods=['GET'])
@require_admin
def get_sections():
    sections = BVASection.query.order_by(BVASection.order, BVASection.id).all()
    return jsonify({'success': True, 'sections': [s.to_dict() for s in sections]})

@bva_bp.route('/api/sections', methods=['POST'])
@require_admin
def create_section():
    data = request.get_json()
    key  = (data.get('key') or '').strip()
    if not key:
        return jsonify({'success': False, 'error': 'key is required'}), 400
    existing = BVASection.query.filter_by(key=key).first()
    if existing:
        return jsonify({'success': False, 'error': f'key "{key}" already exists'}), 400
    max_order = db.session.query(db.func.max(BVASection.order)).scalar() or 0
    section = BVASection(
        key         = key,
        label       = data.get('label', key),
        description = data.get('description', ''),
        color       = data.get('color', '#6366f1'),
        formula     = data.get('formula', '0'),
        order       = max_order + 1,
    )
    db.session.add(section)
    db.session.commit()
    return jsonify({'success': True, 'section': section.to_dict()})

@bva_bp.route('/api/sections/<int:section_id>', methods=['PUT'])
@require_admin
def update_section(section_id):
    section = BVASection.query.get_or_404(section_id)
    data    = request.get_json()
    for f in ['key', 'label', 'description', 'color', 'formula', 'order']:
        if f in data:
            setattr(section, f, data[f])
    db.session.commit()
    return jsonify({'success': True, 'section': section.to_dict()})

@bva_bp.route('/api/sections/<int:section_id>', methods=['DELETE'])
@require_admin
def delete_section(section_id):
    section = BVASection.query.get_or_404(section_id)
    db.session.delete(section)
    db.session.commit()
    return jsonify({'success': True})

@bva_bp.route('/api/sections/reorder', methods=['POST'])
@require_admin
def reorder_sections():
    data = request.get_json()
    for item in data.get('order', []):
        s = BVASection.query.get(item['id'])
        if s:
            s.order = item['order']
    db.session.commit()
    return jsonify({'success': True})

# ── Combined config endpoint for user BVA tab ─────────────────────────────────

@bva_user_bp.route('/<customer_slug>/bva-config', methods=['GET'])
def get_bva_config(customer_slug):
    cfg      = _get_or_create_config()
    sections = BVASection.query.order_by(BVASection.order, BVASection.id).all()

    completed = (UserResponse.query
                 .filter_by(status='completed')
                 .order_by(UserResponse.completed_at.desc())
                 .all())
    user_resp = None
    for r in completed:
        if _make_slug(r.customer_name) == customer_slug:
            user_resp = r
            break

    overrides = {}
    site_count_from_answers = None
    if user_resp:
        raw = user_resp.raw_responses or {}
        for k, v in raw.items():
            if k.startswith('bva_'):
                overrides[k[4:]] = v
        kw      = cfg.site_count_keyword or 'no_of_sites'
        answers = user_resp.answers or {}
        val     = answers.get(kw)
        if val is not None:
            try:
                site_count_from_answers = float(str(val).replace(',', '').strip())
            except (ValueError, TypeError):
                site_count_from_answers = None

    return jsonify({
        'success':                True,
        'config':                 cfg.to_dict(),
        'sections':               [s.to_dict() for s in sections],
        'overrides':              overrides,
        'site_count_from_answers': site_count_from_answers,
    })

# ── Save customer BVA slider overrides ───────────────────────────────────────

@bva_user_bp.route('/<customer_slug>/bva-save', methods=['PATCH'])
def save_bva_overrides(customer_slug):
    data      = request.get_json()
    overrides = data.get('overrides', {})

    completed = (UserResponse.query
                 .filter_by(status='completed')
                 .order_by(UserResponse.completed_at.desc())
                 .all())
    user_resp = None
    for r in completed:
        if _make_slug(r.customer_name) == customer_slug:
            user_resp = r
            break

    if not user_resp:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    raw = dict(user_resp.raw_responses or {})
    for k, v in overrides.items():
        raw[f'bva_{k}'] = v
    user_resp.raw_responses = raw
    db.session.commit()
    return jsonify({'success': True})
