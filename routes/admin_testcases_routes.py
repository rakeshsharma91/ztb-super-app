from flask import Blueprint, request, jsonify, send_file
from models import db, ColumnDefinition
import io

testcases_bp = Blueprint('testcases', __name__)

# ── Use a generic JSON model since TestCase may not exist ─────────────────────
from models import db
from sqlalchemy import text

def get_columns():
    return ColumnDefinition.query.filter_by(table_name='testcases') \
        .order_by(ColumnDefinition.display_order).all()

def key_from_name(name):
    return name.lower().strip().replace(' ', '_').replace('-', '_')

def get_all_rows():
    try:
        from models import TestCase
        cols = get_columns()
        rows = TestCase.query.order_by(TestCase.id).all()
        result = []
        for r in rows:
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            result.append(d)
        return result
    except Exception:
        return []

@testcases_bp.route('/admin/testcases/', methods=['GET'])
def list_rows():
    try:
        from models import TestCase
        cols = get_columns()
        rows = TestCase.query.order_by(TestCase.id).all()
        result = []
        for r in rows:
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            result.append(d)
        return jsonify(result)
    except Exception as e:
        return jsonify([])

@testcases_bp.route('/admin/testcases/', methods=['POST'])
def add_row():
    try:
        from models import TestCase
        data = request.get_json() or {}
        obj = TestCase(
            title    = data.get('title', '')    or '',
            category = data.get('category', '') or '',
            steps    = data.get('steps', '')    or '',
            expected = data.get('expected', '') or '',
            status   = data.get('status', '')   or '',
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

@testcases_bp.route('/admin/testcases/<int:row_id>', methods=['DELETE'])
def delete_row(row_id):
    try:
        from models import TestCase
        obj = TestCase.query.get(row_id)
        if not obj:
            return jsonify({'error': 'Not found'}), 404
        db.session.delete(obj)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@testcases_bp.route('/admin/testcases/cell', methods=['PATCH'])
def update_cell():
    try:
        from models import TestCase
        data  = request.get_json() or {}
        obj   = TestCase.query.get(data.get('id'))
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

@testcases_bp.route('/admin/testcases/columns', methods=['GET'])
def get_cols():
    return jsonify([c.column_key for c in get_columns()])

@testcases_bp.route('/admin/testcases/columns', methods=['POST'])
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
            .filter_by(table_name='testcases').scalar() or 0
        col = ColumnDefinition(table_name='testcases', column_key=key,
            column_label=name, column_type='text',
            display_order=max_order+1, is_active=True, is_required=False)
        db.session.add(col)
        db.session.commit()
        return jsonify([c.column_key for c in get_columns()]), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@testcases_bp.route('/admin/testcases/columns/<string:name>', methods=['DELETE'])
def delete_col(name):
    try:
        col = ColumnDefinition.query.filter_by(
            table_name='testcases', column_key=name).first()
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

@testcases_bp.route('/admin/testcases/column', methods=['PATCH'])
def rename_col():
    try:
        data = request.get_json() or {}
        col  = ColumnDefinition.query.filter_by(
            table_name='testcases', column_key=data.get('oldName')).first()
        if not col:
            return jsonify({'error': 'Not found'}), 404
        col.column_label = data.get('newName')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@testcases_bp.route('/admin/testcases/columns/reorder', methods=['PATCH'])
def reorder_cols():
    try:
        order = (request.get_json() or {}).get('order', [])
        for i, key in enumerate(order):
            col = ColumnDefinition.query.filter_by(
                table_name='testcases', column_key=key).first()
            if col:
                col.display_order = i
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@testcases_bp.route('/admin/testcases/import', methods=['POST'])
def import_rows():
    try:
        from models import TestCase
        rows = (request.get_json() or {}).get('rows', [])
        for row in rows:
            obj = TestCase(
                title    = row.get('title', '')    or '',
                category = row.get('category', '') or '',
                steps    = row.get('steps', '')    or '',
                expected = row.get('expected', '') or '',
                status   = row.get('status', '')   or '',
            )
            db.session.add(obj)
        db.session.commit()
        cols = get_columns()
        result = []
        for r in TestCase.query.order_by(TestCase.id).all():
            d = {'id': r.id}
            for col in cols:
                d[col.column_key] = getattr(r, col.column_key, '') or ''
            result.append(d)
        return jsonify(result)
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@testcases_bp.route('/admin/testcases/export', methods=['GET'])
def export_rows():
    try:
        from models import TestCase
        from openpyxl import Workbook
        cols = get_columns()
        rows = TestCase.query.order_by(TestCase.id).all()
        wb = Workbook(); ws = wb.active; ws.title = 'Test Cases'
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
            as_attachment=True, download_name='testcases_export.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
