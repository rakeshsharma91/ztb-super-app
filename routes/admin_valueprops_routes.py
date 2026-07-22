from flask import Blueprint, request, jsonify, send_file
from models import db, ValueProp, ColumnDefinition
import io
import json

valueprops_bp = Blueprint('valueprops', __name__)

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_columns():
    return ColumnDefinition.query.filter_by(table_name='value_props') \
        .order_by(ColumnDefinition.display_order).all()

SYSTEM_FIELDS = ['title', 'description', 'business_value', 'mandatory']

def vp_to_dict(vp, columns):
    row = {'id': vp.id}
    system_map = {
        'title':          vp.title          or '',
        'description':    vp.description    or '',
        'business_value': vp.business_value or '',
        'mandatory':      vp.mandatory,
    }
    for col in columns:
        row[col.column_key] = system_map.get(col.column_key, '')
    return row

def key_from_name(name):
    return name.lower().strip().replace(' ', '_').replace('-', '_')

# ── GET /admin/valueprops/  →  list all rows ──────────────────────────────────
@valueprops_bp.route('/admin/valueprops/', methods=['GET'])
def list_vps():
    columns = get_columns()
    vps     = ValueProp.query.order_by(ValueProp.id).all()
    return jsonify([vp_to_dict(v, columns) for v in vps])

# ── POST /admin/valueprops/  →  add new row ───────────────────────────────────
@valueprops_bp.route('/admin/valueprops/', methods=['POST'])
def add_vp():
    try:
        data = request.get_json() or {}
        vp = ValueProp(
            title          = data.get('title', '')          or '',
            description    = data.get('description', '')    or '',
            business_value = data.get('business_value', '') or '',
            mandatory      = bool(data.get('mandatory', False))
        )
        db.session.add(vp)
        db.session.commit()
        columns = get_columns()
        return jsonify(vp_to_dict(vp, columns)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── DELETE /admin/valueprops/<id>  →  delete row ─────────────────────────────
@valueprops_bp.route('/admin/valueprops/<int:vp_id>', methods=['DELETE'])
def delete_vp(vp_id):
    try:
        vp = ValueProp.query.get(vp_id)
        if not vp:
            return jsonify({'error': 'Not found'}), 404
        db.session.delete(vp)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── PATCH /admin/valueprops/cell  →  update one cell ─────────────────────────
@valueprops_bp.route('/admin/valueprops/cell', methods=['PATCH'])
def update_cell():
    try:
        data  = request.get_json() or {}
        vp_id = data.get('id')
        field = data.get('field')
        value = data.get('value', '')

        vp = ValueProp.query.get(vp_id)
        if not vp:
            return jsonify({'error': 'Not found'}), 404

        if field in SYSTEM_FIELDS:
            if field == 'mandatory':
                vp.mandatory = bool(value)
            else:
                setattr(vp, field, value)
            db.session.commit()

        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── GET /admin/valueprops/columns  →  list column names ──────────────────────
@valueprops_bp.route('/admin/valueprops/columns', methods=['GET'])
def get_columns_list():
    cols = get_columns()
    return jsonify([c.column_key for c in cols])

# ── POST /admin/valueprops/columns  →  add new column ────────────────────────
@valueprops_bp.route('/admin/valueprops/columns', methods=['POST'])
def add_column():
    try:
        data  = request.get_json() or {}
        name  = data.get('name', 'New Column')
        key   = key_from_name(name)

        existing = [c.column_key for c in get_columns()]
        base = key
        i = 1
        while key in existing:
            key = f"{base}_{i}"
            i += 1

        max_order = db.session.query(db.func.max(ColumnDefinition.display_order)) \
            .filter_by(table_name='value_props').scalar() or 0

        col = ColumnDefinition(
            table_name    = 'value_props',
            column_key    = key,
            column_label  = name,
            column_type   = 'text',
            display_order = max_order + 1,
            is_active     = True,
            is_required   = False
        )
        db.session.add(col)
        db.session.commit()
        cols = get_columns()
        return jsonify([c.column_key for c in cols]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── DELETE /admin/valueprops/columns/<name>  →  delete column ────────────────
@valueprops_bp.route('/admin/valueprops/columns/<string:name>', methods=['DELETE'])
def delete_column(name):
    try:
        col = ColumnDefinition.query.filter_by(
            table_name='value_props', column_key=name
        ).first()
        if not col:
            return jsonify({'error': 'Column not found'}), 404
        if col.is_required:
            return jsonify({'error': 'Cannot delete a required column'}), 400
        db.session.delete(col)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── PATCH /admin/valueprops/column  →  rename column ─────────────────────────
@valueprops_bp.route('/admin/valueprops/column', methods=['PATCH'])
def rename_column():
    try:
        data     = request.get_json() or {}
        old_name = data.get('oldName')
        new_name = data.get('newName')

        col = ColumnDefinition.query.filter_by(
            table_name='value_props', column_key=old_name
        ).first()
        if not col:
            return jsonify({'error': 'Column not found'}), 404

        col.column_label = new_name
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── PATCH /admin/valueprops/columns/reorder  →  reorder columns ──────────────
@valueprops_bp.route('/admin/valueprops/columns/reorder', methods=['PATCH'])
def reorder_columns():
    try:
        data  = request.get_json() or {}
        order = data.get('order', [])
        for i, key in enumerate(order):
            col = ColumnDefinition.query.filter_by(
                table_name='value_props', column_key=key
            ).first()
            if col:
                col.display_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── POST /admin/valueprops/import  →  import rows from Excel ─────────────────
@valueprops_bp.route('/admin/valueprops/import', methods=['POST'])
def import_vps():
    try:
        data = request.get_json() or {}
        rows = data.get('rows', [])
        for row in rows:
            vp = ValueProp(
                title          = row.get('title', '')          or '',
                description    = row.get('description', '')    or '',
                business_value = row.get('business_value', '') or '',
                mandatory      = bool(row.get('mandatory', False))
            )
            db.session.add(vp)
        db.session.commit()
        columns = get_columns()
        vps     = ValueProp.query.order_by(ValueProp.id).all()
        return jsonify([vp_to_dict(v, columns) for v in vps])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ── GET /admin/valueprops/export  →  export as Excel ─────────────────────────
@valueprops_bp.route('/admin/valueprops/export', methods=['GET'])
def export_vps():
    try:
        import openpyxl
        from openpyxl import Workbook
        columns = get_columns()
        vps     = ValueProp.query.order_by(ValueProp.id).all()

        wb = Workbook()
        ws = wb.active
        ws.title = 'Value Props'

        headers = [c.column_key for c in columns]
        ws.append(headers)

        for vp in vps:
            row = vp_to_dict(vp, columns)
            ws.append([row.get(h, '') for h in headers])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='valueprops_export.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
