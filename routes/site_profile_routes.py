from flask import Blueprint, request, jsonify, session
from models import db, TCOEntry, PricingSKU, AdminConfig, UserResponse
from functools import wraps
import re

site_profile_bp = Blueprint('site_profile', __name__)

TCO_CATEGORIES = ['fw_ns', 'sdwan', 'mpls', 'fw_ew', 'iot_ot', 'nac', 'l3sw', 'pam']
TCO_LABELS = {
    'fw_ns':  'FW N/S',
    'sdwan':  'SD-WAN',
    'mpls':   'MPLS',
    'fw_ew':  'FW E/W',
    'iot_ot': 'IoT/OT',
    'nac':    'NAC',
    'l3sw':   'L3 Switch',
    'pam':    'PAM',
}

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


# ── GET /api/site-profile-config ──────────────────────────────────────────────
# Returns everything the Site Profile Builder needs to render:
#   - vendors per TCO category (deduplicated list)
#   - guidance text from AdminConfig
#   - saved site profile rows (if customer_slug provided)
# ─────────────────────────────────────────────────────────────────────────────
@site_profile_bp.route('/api/site-profile-config', methods=['GET'])
def site_profile_config():
    # Build vendors per category (unique, ordered by display_order)
    entries = (TCOEntry.query
               .filter_by(active=True)
               .order_by(TCOEntry.category, TCOEntry.display_order, TCOEntry.id)
               .all())

    vendors = {cat: [] for cat in TCO_CATEGORIES}
    seen    = {cat: set() for cat in TCO_CATEGORIES}
    for e in entries:
        if e.category in vendors and e.vendor not in seen[e.category]:
            vendors[e.category].append(e.vendor)
            seen[e.category].add(e.vendor)

    # Guidance text
    guidance_row = AdminConfig.query.filter_by(key='site_profile_guidance').first()
    guidance = guidance_row.value if guidance_row else (
        'Define your customer\'s site profile below. Each row represents a site tier '
        '(e.g. Small Branch, Factory, Data Centre). The size you select drives automatic '
        'SKU selection in the Pricing and TCO tabs. Check SD-WAN Required if the site '
        'needs an SD-WAN license, Segmentation Required if micro-segmentation is needed, '
        'and HA Required to select the dual-appliance SKU.'
    )

    # Saved rows (optional — pass ?slug=customer-slug)
    slug      = request.args.get('slug', '')
    saved     = []
    if slug:
        user_resp = _find_user_resp(slug)
        if user_resp:
            raw  = user_resp.raw_responses or {}
            saved = raw.get('site_profile', [])

    return jsonify({
        'success':          True,
        'vendors':          vendors,
        'category_labels':  TCO_LABELS,
        'guidance':         guidance,
        'saved':            saved,
    })


# ── PATCH /user/<customer_slug>/site-profile-save ────────────────────────────
@site_profile_bp.route('/user/<customer_slug>/site-profile-save', methods=['PATCH'])
def site_profile_save(customer_slug):
    data  = request.get_json() or {}
    rows  = data.get('rows', [])

    user_resp = _find_user_resp(customer_slug)
    if not user_resp:
        # During assessment flow the record may be a draft — look up by session
        draft_id  = session.get('draft_response_id')
        user_resp = UserResponse.query.get(draft_id) if draft_id else None

    if not user_resp:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404

    raw = dict(user_resp.raw_responses or {})
    raw['site_profile'] = rows
    user_resp.raw_responses = raw
    db.session.commit()
    return jsonify({'success': True})
