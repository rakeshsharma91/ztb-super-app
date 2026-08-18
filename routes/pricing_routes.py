from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from models import db, PricingSKU, UserResponse
import re

pricing_bp      = Blueprint('pricing', __name__)
pricing_user_bp = Blueprint('pricing_user', __name__)

VALID_SIZES = ('Small', 'Medium', 'Large', 'XL')

# ── Auth helper ───────────────────────────────────────────────────────────────
def admin_required():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    return None


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — Pricing Grid page
# ══════════════════════════════════════════════════════════════════════════════

@pricing_bp.route('/admin/pricing/')
def pricing_grid():
    redir = admin_required()
    if redir:
        return redir
    return render_template('pricing.html')


# ── GET all SKUs ──────────────────────────────────────────────────────────────
@pricing_bp.route('/admin/pricing/api/skus', methods=['GET'])
def get_skus():
    redir = admin_required()
    if redir:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    skus = PricingSKU.query.order_by(PricingSKU.display_order, PricingSKU.id).all()
    return jsonify({'success': True, 'skus': [s.to_dict() for s in skus]})


# ── CREATE SKU ────────────────────────────────────────────────────────────────
@pricing_bp.route('/admin/pricing/api/skus', methods=['POST'])
def create_sku():
    redir = admin_required()
    if redir:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    data = request.get_json() or {}
    raw_size = data.get('size') or None
    sku = PricingSKU(
        sku_code      = data.get('sku_code', '').strip(),
        sku_name      = data.get('sku_name', '').strip(),
        category      = data.get('category', 'appliance'),
        size          = raw_size if raw_size in VALID_SIZES else None,
        cogs          = float(data.get('cogs', 0) or 0),
        list_price    = float(data.get('list_price', 0) or 0),
        budgetary     = float(data.get('budgetary', 0) or 0),
        standard      = float(data.get('standard', 0) or 0),
        aggressive    = float(data.get('aggressive', 0) or 0),
        is_ha         = bool(data.get('is_ha', False)),
        ha_parent_id  = int(data['ha_parent_id']) if data.get('ha_parent_id') else None,
        display_order = int(data.get('display_order', 99) or 99),
        active        = bool(data.get('active', True)),
    )
    db.session.add(sku)
    db.session.commit()
    return jsonify({'success': True, 'sku': sku.to_dict()})


# ── UPDATE SKU ────────────────────────────────────────────────────────────────
@pricing_bp.route('/admin/pricing/api/skus/<int:sku_id>', methods=['PUT'])
def update_sku(sku_id):
    redir = admin_required()
    if redir:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    sku = PricingSKU.query.get_or_404(sku_id)
    data = request.get_json() or {}

    if 'sku_code'      in data: sku.sku_code      = data['sku_code'].strip()
    if 'sku_name'      in data: sku.sku_name      = data['sku_name'].strip()
    if 'category'      in data: sku.category      = data['category']
    if 'size'          in data:
        raw_size = data['size'] or None
        sku.size = raw_size if raw_size in VALID_SIZES else None
    if 'cogs'          in data: sku.cogs          = float(data['cogs'] or 0)
    if 'list_price'    in data: sku.list_price    = float(data['list_price'] or 0)
    if 'budgetary'     in data: sku.budgetary     = float(data['budgetary'] or 0)
    if 'standard'      in data: sku.standard      = float(data['standard'] or 0)
    if 'aggressive'    in data: sku.aggressive    = float(data['aggressive'] or 0)
    if 'is_ha'         in data: sku.is_ha         = bool(data['is_ha'])
    if 'ha_parent_id'  in data: sku.ha_parent_id  = int(data['ha_parent_id']) if data['ha_parent_id'] else None
    if 'display_order' in data: sku.display_order = int(data['display_order'] or 0)
    if 'active'        in data: sku.active        = bool(data['active'])

    # If this is a No-HA appliance and auto_ha is requested, update the linked HA child
    if data.get('sync_ha') and not sku.is_ha:
        ha_child = PricingSKU.query.filter_by(ha_parent_id=sku.id, is_ha=True).first()
        if ha_child:
            ha_child.list_price = sku.list_price * 2
            ha_child.budgetary  = sku.budgetary  * 2
            ha_child.standard   = sku.standard   * 2
            ha_child.aggressive = sku.aggressive * 2
            ha_child.cogs       = sku.cogs       * 2

    db.session.commit()
    return jsonify({'success': True, 'sku': sku.to_dict()})


# ── DELETE (deactivate) SKU ───────────────────────────────────────────────────
@pricing_bp.route('/admin/pricing/api/skus/<int:sku_id>', methods=['DELETE'])
def delete_sku(sku_id):
    redir = admin_required()
    if redir:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    sku = PricingSKU.query.get_or_404(sku_id)
    sku.active = False
    db.session.commit()
    return jsonify({'success': True})


# ── HARD DELETE SKU ───────────────────────────────────────────────────────────
@pricing_bp.route('/admin/pricing/api/skus/<int:sku_id>/hard', methods=['DELETE'])
def hard_delete_sku(sku_id):
    redir = admin_required()
    if redir:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    sku = PricingSKU.query.get_or_404(sku_id)
    db.session.delete(sku)
    db.session.commit()
    return jsonify({'success': True})


# ══════════════════════════════════════════════════════════════════════════════
# USER — Pricing tab on customer results page
# ══════════════════════════════════════════════════════════════════════════════

def _slug_to_response(customer_slug):
    """Return the UserResponse for a slug (same logic as user_routes)."""
    name = customer_slug.replace('-', ' ')
    resp = UserResponse.query.filter(
        db.func.lower(UserResponse.customer_name) == name.lower(),
        UserResponse.status == 'completed'
    ).order_by(UserResponse.completed_at.desc()).first()
    return resp


# ── GET pricing config (SKUs + saved rows for this customer) ─────────────────
@pricing_user_bp.route('/user/<customer_slug>/pricing-config', methods=['GET'])
def pricing_config(customer_slug):
    # All active SKUs grouped by category
    skus = PricingSKU.query.filter_by(active=True).order_by(
        PricingSKU.display_order, PricingSKU.id
    ).all()

    appliances   = [s.to_dict() for s in skus if s.category == 'appliance']
    sdwan        = [s.to_dict() for s in skus if s.category == 'sdwan']
    segmentation = [s.to_dict() for s in skus if s.category == 'segmentation']

    # Saved pricing data for this customer
    saved = {}
    resp = _slug_to_response(customer_slug)
    if resp and resp.pricing_data:
        saved = resp.pricing_data

    return jsonify({
        'success':      True,
        'appliances':   appliances,
        'sdwan':        sdwan,
        'segmentation': segmentation,
        'saved':        saved,   # { phase, rows: [...] }
    })


# ── SAVE pricing inputs for this customer ────────────────────────────────────
@pricing_user_bp.route('/user/<customer_slug>/pricing-save', methods=['PATCH'])
def pricing_save(customer_slug):
    data = request.get_json() or {}
    resp = _slug_to_response(customer_slug)
    if not resp:
        return jsonify({'success': False, 'error': 'Customer not found'}), 404

    resp.pricing_data = {
        'phase': data.get('phase', 'standard'),
        'rows':  data.get('rows', []),
    }
    db.session.commit()
    return jsonify({'success': True})
