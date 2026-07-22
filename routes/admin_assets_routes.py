from flask import Blueprint, request, jsonify, send_file
from models import db, Asset, ColumnDefinition
import io

assets_bp = Blueprint('assets', __name__)

def get_columns():
    return ColumnDefinition.query.filter_by(table_name='assets') \
        .order_by(ColumnDefinition.display_order).all()

SYSTEM_FIELDS = ['title', 'asset_type', 'url', 'description']

def row_to_dict(obj, columns):
    row = {'id': obj.id}
    system_map = {
        'title':       obj.title       or '',
        'asset_type':  obj.asset_type  or '',
        'url':         obj.url         or '',
        'description': obj.description or '',
    }
    for col in columns:
        row[col.column_key] = system_map.get(col.column_key, '')
    return row

def key_from_name(name):
    return name.lower().strip().replace(' ', '_').replace('-', '_')

@assets_bp.route('/admin/assets/', methods=['GET'])
def list_rows():
    cols = get_columns()
    rows = Asset.query.order_by(Asset.id).all()
    return jsonify([row_to_dict(r, cols) for r in rows])

@assets_bp.route('/admin/assets/', methods=['POST'])
def add_row():
    try:
        data = request.get_json() or {}
        obj = Asset(
            title       = data.get('title', '')       or '',
            asset_type  = data.get('asset_type', '')  or '',
            url         = data.get('url', '')         or '',
            description = data.get('description', '') or '',
        )
        db.session.add(obj)
        db.session.commit()
        return jsonify(row_to_dict(obj, get_columns())), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/<int:row_id>', methods=['DELETE'])
def delete_row(row_id):
    try:
        obj = Asset.query.get(row_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        db.session.delete(obj)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/cell', methods=['PATCH'])
def update_cell():
    try:
        data  = request.get_json() or {}
        obj   = Asset.query.get(data.get('id'))
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        field = data.get('field')
        value = data.get('value', '')
        if field in SYSTEM_FIELDS:
            setattr(obj, field, value)
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/columns', methods=['GET'])
def get_cols():
    return jsonify([c.column_key for c in get_columns()])

@assets_bp.route('/admin/assets/columns', methods=['POST'])
def add_col():
    try:
        data = request.get_json() or {}
        name = data.get('name', 'New Column')
        key  = key_from_name(name)
        existing = [c.column_key for c in get_columns()]
        base = key; i = 1
        while key in existing:
            key = f"{base}_{i}"; i += 1
        max_order = db.session.query(db.func.max(ColumnDefinition.display_order)) \
            .filter_by(table_name='assets').scalar() or 0
        col = ColumnDefinition(table_name='assets', column_key=key,
            column_label=name, column_type='text',
            display_order=max_order+1, is_active=True, is_required=False)
        db.session.add(col)
        db.session.commit()
        return jsonify([c.column_key for c in get_columns()]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/columns/<string:name>', methods=['DELETE'])
def delete_col(name):
    try:
        col = ColumnDefinition.query.filter_by(table_name='assets', column_key=name).first()
        if not col:
            return jsonify({'error': 'Not found'}), 404
        if col.is_required:
            return jsonify({'error': 'Cannot delete required column'}), 400
        db.session.delete(col)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/column', methods=['PATCH'])
def rename_col():
    try:
        data = request.get_json() or {}
        col  = ColumnDefinition.query.filter_by(
            table_name='assets', column_key=data.get('oldName')).first()
        if not col:
            return jsonify({'error': 'Not found'}), 404
        col.column_label = data.get('newName')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/columns/reorder', methods=['PATCH'])
def reorder_cols():
    try:
        order = (request.get_json() or {}).get('order', [])
        for i, key in enumerate(order):
            col = ColumnDefinition.query.filter_by(
                table_name='assets', column_key=key).first()
            if col:
                col.display_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/import', methods=['POST'])
def import_rows():
    try:
        rows = (request.get_json() or {}).get('rows', [])
        for row in rows:
            obj = Asset(
                title       = row.get('title', '')       or '',
                asset_type  = row.get('asset_type', '')  or '',
                url         = row.get('url', '')         or '',
                description = row.get('description', '') or '',
            )
            db.session.add(obj)
        db.session.commit()
        cols = get_columns()
        return jsonify([row_to_dict(r, cols) for r in Asset.query.order_by(Asset.id).all()])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@assets_bp.route('/admin/assets/export', methods=['GET'])
def export_rows():
    try:
        from openpyxl import Workbook
        cols = get_columns()
        rows = Asset.query.order_by(Asset.id).all()
        wb = Workbook(); ws = wb.active; ws.title = 'Assets'
        headers = [c.column_key for c in cols]
        ws.append(headers)
        for r in rows:
            d = row_to_dict(r, cols)
            ws.append([d.get(h, '') for h in headers])
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return send_file(buf,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, download_name='assets_export.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
