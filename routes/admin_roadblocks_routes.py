from flask import Blueprint, request, jsonify, send_file
from models import db, ColumnDefinition
import io

roadblocks_bp = Blueprint('roadblocks', __name__)

def get_columns():
    return ColumnDefinition.query.filter_by(table_name='roadblocks') \
        .order_by(ColumnDefinition.display_order).all()

def key_from_name(name):
    return name.lower().strip().replace(' ', '_').replace('-', '_')

@roadblocks_bp.route('/admin/roadblocks/', methods=['GET'])
def list_rows():
    try:
        from models import Roadblock
        cols = get_columns()
        rows = Roadblock.query.order_by(Roadblock.id).all()
        result = []
        for r in rows:
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            result.append(d)
        return jsonify(result)
    except Exception:
        return jsonify([])

@roadblocks_bp.route('/admin/roadblocks/', methods=['POST'])
def add_row():
    try:
        from models import Roadblock
        data = request.get_json() or {}
        obj = Roadblock(
            title       = data.get('title', '')       or '',
            description = data.get('description', '') or '',
            owner       = data.get('owner', '')       or '',
            priority    = data.get('priority', '')    or '',
            status      = data.get('status', '')      or '',
        )
        db.session.add(obj)
        db.session.commit()
        cols = get_columns()
        d = {'id': obj.id}
        for col in cols:
            d[col.column_key] = getattr(obj, col.column_key, '') or ''
        return jsonify(d), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/<int:row_id>', methods=['DELETE'])
def delete_row(row_id):
    try:
        from models import Roadblock
        obj = Roadblock.query.get(row_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        db.session.delete(obj)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/cell', methods=['PATCH'])
def update_cell():
    try:
        from models import Roadblock
        data  = request.get_json() or {}
        obj   = Roadblock.query.get(data.get('id'))
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        field = data.get('field')
        value = data.get('value', '')
        if hasattr(obj, field):
            setattr(obj, field, value)
            db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/columns', methods=['GET'])
def get_cols():
    return jsonify([c.column_key for c in get_columns()])

@roadblocks_bp.route('/admin/roadblocks/columns', methods=['POST'])
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
            .filter_by(table_name='roadblocks').scalar() or 0
        col = ColumnDefinition(table_name='roadblocks', column_key=key,
            column_label=name, column_type='text',
            display_order=max_order+1, is_active=True, is_required=False)
        db.session.add(col)
        db.session.commit()
        return jsonify([c.column_key for c in get_columns()]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/columns/<string:name>', methods=['DELETE'])
def delete_col(name):
    try:
        col = ColumnDefinition.query.filter_by(
            table_name='roadblocks', column_key=name).first()
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

@roadblocks_bp.route('/admin/roadblocks/column', methods=['PATCH'])
def rename_col():
    try:
        data = request.get_json() or {}
        col  = ColumnDefinition.query.filter_by(
            table_name='roadblocks', column_key=data.get('oldName')).first()
        if not col:
            return jsonify({'error': 'Not found'}), 404
        col.column_label = data.get('newName')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/columns/reorder', methods=['PATCH'])
def reorder_cols():
    try:
        order = (request.get_json() or {}).get('order', [])
        for i, key in enumerate(order):
            col = ColumnDefinition.query.filter_by(
                table_name='roadblocks', column_key=key).first()
            if col:
                col.display_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/import', methods=['POST'])
def import_rows():
    try:
        from models import Roadblock
        rows = (request.get_json() or {}).get('rows', [])
        for row in rows:
            obj = Roadblock(
                title       = row.get('title', '')       or '',
                description = row.get('description', '') or '',
                owner       = row.get('owner', '')       or '',
                priority    = row.get('priority', '')    or '',
                status      = row.get('status', '')      or '',
            )
            db.session.add(obj)
        db.session.commit()
        cols = get_columns()
        result = []
        for r in Roadblock.query.order_by(Roadblock.id).all():
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            result.append(d)
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@roadblocks_bp.route('/admin/roadblocks/export', methods=['GET'])
def export_rows():
    try:
        from models import Roadblock
        from openpyxl import Workbook
        cols = get_columns()
        rows = Roadblock.query.order_by(Roadblock.id).all()
        wb = Workbook(); ws = wb.active; ws.title = 'Roadblocks'
        headers = [c.column_key for c in cols]
        ws.append(headers)
        for r in rows:
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            ws.append([d.get(h, '') for h in headers])
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return send_file(buf,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, download_name='roadblocks_export.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
