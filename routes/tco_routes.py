from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models import db, TCOEntry, TCOConfig, UserResponse
from functools import wraps
import re

tco_bp      = Blueprint('tco',      __name__, url_prefix='/admin/tco')
tco_user_bp = Blueprint('tco_user', __name__, url_prefix='/user')

TCO_CATEGORIES = ['fw_ns', 'sdwan', 'mpls', 'fw_ew', 'iot_ot', 'nac', 'l3sw', 'pam']
TCO_CATEGORY_LABELS = {
    'fw_ns':  'FW N/S (Outbound Firewall)',
    'sdwan':  'SD-WAN / Edge',
    'mpls':   'MPLS / WAN Circuits',
    'fw_ew':  'FW E/W (Micro-Segmentation)',
    'iot_ot': 'IoT / OT Security',
    'nac':    'NAC',
    'l3sw':   'L3 Switching',
    'pam':    'PAM',
}

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

def _find_user_resp(customer_slug):
    completed = (UserResponse.query
                 .filter_by(status='completed')
                 .order_by(UserResponse.completed_at.desc())
                 .all())
    for r in completed:
        if _make_slug(r.customer_name) == customer_slug:
            return r
    return None

def _get_or_create_tco_config():
    cfg = TCOConfig.query.get(1)
    if not cfg:
        cfg = TCOConfig(id=1, fte_count=6.0, fte_cost=120000.0, breach_cost=4450000.0)
        db.session.add(cfg)
        db.session.commit()
    return cfg

# ── Admin page ────────────────────────────────────────────────────────────────

@tco_bp.route('/', methods=['GET'])
def tco_page():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login_page'))
    return render_template('tco.html')

# ── Admin API: TCO Config (defaults) ─────────────────────────────────────────

@tco_bp.route('/api/config', methods=['GET'])
@require_admin
def get_config():
    cfg = _get_or_create_tco_config()
    return jsonify({'success': True, 'config': cfg.to_dict()})

@tco_bp.route('/api/config', methods=['PUT'])
@require_admin
def update_config():
    cfg  = _get_or_create_tco_config()
    data = request.get_json()
    if 'fte_count' in data:
        cfg.fte_count   = float(data['fte_count']   or 0)
    if 'fte_cost' in data:
        cfg.fte_cost    = float(data['fte_cost']    or 0)
    if 'breach_cost' in data:
        cfg.breach_cost = float(data['breach_cost'] or 0)
    db.session.commit()
    return jsonify({'success': True, 'config': cfg.to_dict()})

# ── Admin API: TCO Entries ────────────────────────────────────────────────────

@tco_bp.route('/api/entries', methods=['GET'])
@require_admin
def get_entries():
    cat = request.args.get('category')
    q   = TCOEntry.query.filter_by(active=True)
    if cat:
        q = q.filter_by(category=cat)
    entries = q.order_by(TCOEntry.category, TCOEntry.display_order, TCOEntry.id).all()
    grouped = {c: [] for c in TCO_CATEGORIES}
    for e in entries:
        if e.category in grouped:
            grouped[e.category].append(e.to_dict())
    return jsonify({'success': True, 'entries': grouped, 'category_labels': TCO_CATEGORY_LABELS})

@tco_bp.route('/api/entries', methods=['POST'])
@require_admin
def create_entry():
    data     = request.get_json()
    category = (data.get('category') or '').strip()
    vendor   = (data.get('vendor')   or '').strip()
    size     = (data.get('size')     or '').strip()
    sku_name = (data.get('sku_name') or '').strip()
    if not category or category not in TCO_CATEGORIES:
        return jsonify({'success': False, 'error': f'Invalid category: {category}'}), 400
    if not vendor or not size or not sku_name:
        return jsonify({'success': False, 'error': 'vendor, size and sku_name are required'}), 400
    max_order = (db.session.query(db.func.max(TCOEntry.display_order))
                 .filter_by(category=category).scalar() or 0)
    entry = TCOEntry(
        category      = category,
        vendor        = vendor,
        size          = size,
        sku_name      = sku_name,
        annual_cost   = float(data.get('annual_cost') or 0),
        display_order = max_order + 1,
        active        = True,
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'success': True, 'entry': entry.to_dict()})

@tco_bp.route('/api/entries/<int:entry_id>', methods=['PUT'])
@require_admin
def update_entry(entry_id):
    entry = TCOEntry.query.get_or_404(entry_id)
    data  = request.get_json()
    for f in ['vendor', 'size', 'sku_name', 'display_order']:
        if f in data:
            setattr(entry, f, data[f])
    if 'annual_cost' in data:
        entry.annual_cost = float(data['annual_cost'] or 0)
    if 'category' in data and data['category'] in TCO_CATEGORIES:
        entry.category = data['category']
    db.session.commit()
    return jsonify({'success': True, 'entry': entry.to_dict()})

@tco_bp.route('/api/entries/<int:entry_id>', methods=['DELETE'])
@require_admin
def delete_entry(entry_id):
    entry = TCOEntry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'success': True})

# ── User API: load TCO config for a customer ──────────────────────────────────

@tco_user_bp.route('/<customer_slug>/tco-config', methods=['GET'])
def get_tco_config(customer_slug):
    entries = (TCOEntry.query
               .filter_by(active=True)
               .order_by(TCOEntry.category, TCOEntry.display_order, TCOEntry.id)
               .all())
    grouped = {c: [] for c in TCO_CATEGORIES}
    for e in entries:
        if e.category in grouped:
            grouped[e.category].append(e.to_dict())

    cfg = _get_or_create_tco_config()

    user_resp    = _find_user_resp(customer_slug)
    saved_rows   = []
    acv_override = None
    # per-customer overrides for the three hero inputs
    tco_fte_count   = None
    tco_fte_cost    = None
    tco_breach_cost = None

    if user_resp:
        raw = user_resp.raw_responses or {}
        saved_rows      = raw.get('tco_rows',       [])
        acv_override    = raw.get('tco_acv_override')
        tco_fte_count   = raw.get('tco_fte_count')
        tco_fte_cost    = raw.get('tco_fte_cost')
        tco_breach_cost = raw.get('tco_breach_cost')

    return jsonify({
        'success':         True,
        'entries':         grouped,
        'category_labels': TCO_CATEGORY_LABELS,
        'defaults': {
            'fte_count':   cfg.fte_count,
            'fte_cost':    cfg.fte_cost,
            'breach_cost': cfg.breach_cost,
        },
        'saved': {
            'rows':         saved_rows,
            'acv_override': acv_override,
            'fte_count':    tco_fte_count,
            'fte_cost':     tco_fte_cost,
            'breach_cost':  tco_breach_cost,
        },
    })

# ── User API: save TCO rows + hero metric overrides ───────────────────────────

@tco_user_bp.route('/<customer_slug>/tco-save', methods=['PATCH'])
def save_tco(customer_slug):
    data         = request.get_json()
    rows         = data.get('rows', [])
    acv_override = data.get('acv_override')
    fte_count    = data.get('fte_count')
    fte_cost     = data.get('fte_cost')
    breach_cost  = data.get('breach_cost')

    user_resp = _find_user_resp(customer_slug)
    if not user_resp:
        return jsonify({'success': False, 'error': 'Not found'}), 404

    raw = dict(user_resp.raw_responses or {})
    raw['tco_rows'] = rows

    if acv_override is not None:
        raw['tco_acv_override'] = acv_override
    else:
        raw.pop('tco_acv_override', None)

    # Always persist hero metric values (even if they equal the default)
    # so we can restore them on reload
    if fte_count is not None:
        raw['tco_fte_count'] = fte_count
    if fte_cost is not None:
        raw['tco_fte_cost'] = fte_cost
    if breach_cost is not None:
        raw['tco_breach_cost'] = breach_cost

    user_resp.raw_responses = raw
    db.session.commit()
    return jsonify({'success': True})
