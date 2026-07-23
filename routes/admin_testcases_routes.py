from flask import Blueprint, request, jsonify, send_file
from models import db, ColumnDefinition
from sqlalchemy import text
import io

TABLE    = 'test_cases'
BP_NAME  = 'admin_testcases'
URL_BASE = '/admin/testcases'
bp = Blueprint(BP_NAME, __name__)

DEFAULT_COLUMNS = ['Test Case Name', 'Milestones', 'Result', 'Notes', 'Mandatory']
DEFAULT_KEYS    = ['test_case_name', 'test_steps', 'result', 'notes', 'mandatory']

def get_col_defs():
    cols = ColumnDefinition.query.filter_by(table_name=TABLE).order_by(ColumnDefinition.display_order).all()
    if not cols:
        _init_defaults()
        cols = ColumnDefinition.query.filter_by(table_name=TABLE).order_by(ColumnDefinition.display_order).all()
    return cols

def _init_defaults():
    for i, (label, key) in enumerate(zip(DEFAULT_COLUMNS, DEFAULT_KEYS), 1):
        if not ColumnDefinition.query.filter_by(table_name=TABLE, column_key=key).first():
            db.session.add(ColumnDefinition(table_name=TABLE, column_key=key, column_label=label,
                column_type='text', display_order=i, is_active=True, is_required=False))
    db.session.commit()

def key_from_label(label):
    return label.strip().lower().replace(' ', '_').replace('-', '_').replace('/', '_').replace('?', '')

def get_all_rows():
    result = db.session.execute(text(f"SELECT * FROM {TABLE} ORDER BY id"))
    keys = list(result.keys())
    return [dict(zip(keys, row)) for row in result.fetchall()]

@bp.route(URL_BASE + '/', methods=['GET'])
def list_rows():
    try:
        cols = get_col_defs()
        col_names = [c.column_label for c in cols]
        raw_rows = get_all_rows()
        remapped = []
        for row in raw_rows:
            new_row = {"id": row.get("id")}
            for c in cols:
                new_row[c.column_label] = row.get(c.column_key)
            remapped.append(new_row)
        return jsonify({"rows": remapped, "columns": col_names})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/', methods=['POST'])
def add_row():
    try:
        cols = get_col_defs()
        keys = [c.column_key for c in cols if c.column_key not in ('id','created_at','updated_at')]
        if not keys:
            return jsonify({"error": "No columns defined"}), 400
        params = {k: None for k in keys}
        result = db.session.execute(
            text(f"INSERT INTO {TABLE} ({', '.join(keys)}) VALUES ({', '.join([':'+k for k in keys])}) RETURNING id"),
            params
        )
        db.session.commit()
        new_id = result.fetchone()[0]
        raw = db.session.execute(text(f"SELECT * FROM {TABLE} WHERE id = :id"), {"id": new_id}).fetchone()
        raw_dict = dict(raw._mapping) if raw else {}
        new_row = {"id": new_id}
        for c in cols:
            new_row[c.column_label] = raw_dict.get(c.column_key)
        return jsonify(new_row), 201
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/<int:row_id>', methods=['DELETE'])
def delete_row(row_id):
    try:
        # NULL out FK references before deleting
        db.session.execute(text("UPDATE question_options SET test_case_id = NULL WHERE test_case_id = :id"), {"id": row_id})
        db.session.execute(text(f"DELETE FROM {TABLE} WHERE id = :id"), {"id": row_id})
        db.session.commit(); return jsonify({"success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/cell', methods=['PATCH'])
def update_cell():
    try:
        data = request.json or {}
        row_id = data.get("id")
        field  = data.get("field", "").strip()
        value  = data.get("value", "")
        if not row_id or not field:
            return jsonify({"error": "id and field required"}), 400
        col = ColumnDefinition.query.filter_by(table_name=TABLE, column_label=field).first()
        if not col:
            col = ColumnDefinition.query.filter_by(table_name=TABLE, column_key=field).first()
        if not col:
            return jsonify({"error": f"Unknown field: {field}"}), 400
        db.session.execute(
            text(f"UPDATE {TABLE} SET {col.column_key} = :value WHERE id = :id"),
            {"value": value, "id": row_id}
        )
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/columns', methods=['POST'])
def add_column():
    try:
        name = (request.json or {}).get("name", "").strip()
        if not name: return jsonify({"error": "name required"}), 400
        key = key_from_label(name)
        existing = [c.column_key for c in get_col_defs()]
        base, i = key, 1
        while key in existing: key = f"{base}_{i}"; i += 1
        db.session.execute(text(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS {key} TEXT"))
        if not ColumnDefinition.query.filter_by(table_name=TABLE, column_key=key).first():
            max_o = db.session.execute(text("SELECT COALESCE(MAX(display_order),0) FROM column_definitions WHERE table_name=:t"), {"t": TABLE}).scalar()
            db.session.add(ColumnDefinition(table_name=TABLE, column_key=key, column_label=name,
                column_type='text', display_order=max_o+1, is_active=True, is_required=False))
        db.session.commit()
        return jsonify({"success": True, "name": name, "key": key}), 201
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/columns/<path:col_name>', methods=['DELETE'])
def delete_column(col_name):
    try:
        PROTECTED = {'id', 'created_at', 'updated_at'}
        col = ColumnDefinition.query.filter_by(table_name=TABLE, column_label=col_name).first()
        if not col:
            col = ColumnDefinition.query.filter_by(table_name=TABLE, column_key=col_name).first()
        if not col:
            return jsonify({"error": f"Column not found: {col_name}"}), 404
        if col.column_key in PROTECTED:
            return jsonify({"error": f"Cannot delete system column: {col.column_key}"}), 400
        db.session.delete(col)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/column', methods=['PATCH'])
def rename_column():
    try:
        data = request.json or {}
        old_name = (data.get('old_name') or data.get('oldName') or data.get('old_label') or data.get('oldLabel') or '').strip()
        new_name = (data.get('new_name') or data.get('newName') or data.get('new_label') or data.get('newLabel') or '').strip()
        if not old_name or not new_name:
            return jsonify({"error": f"oldName and newName required, got: {list(data.keys())}"}), 400
        col = ColumnDefinition.query.filter_by(table_name=TABLE, column_label=old_name).first()
        if not col:
            col = ColumnDefinition.query.filter_by(table_name=TABLE, column_key=old_name).first()
        if not col:
            return jsonify({"error": f"Column not found: {old_name}"}), 404
        col.column_label = new_name
        db.session.commit()
        return jsonify({"success": True, "old": old_name, "new": new_name})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/columns/reorder', methods=['PATCH'])
def reorder_columns():
    try:
        for i, name in enumerate((request.json or {}).get("order", []), 1):
            col = ColumnDefinition.query.filter_by(table_name=TABLE, column_label=name).first()
            if col: col.display_order = i
        db.session.commit(); return jsonify({"success": True})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/import', methods=['POST'])
def import_rows():
    try:
        rows = (request.json or {}).get("rows", [])
        cols = get_col_defs()
        l2k  = {c.column_label.lower(): c.column_key for c in cols}
        SKIP = {'id', 'ID', 'Id'}
        count = 0
        for row in rows:
            params = {}
            for h, v in row.items():
                if h in SKIP: continue
                k = l2k.get(h.lower(), key_from_label(h))
                params[k] = str(v) if v is not None else ''
            if params:
                keys = list(params.keys())
                db.session.execute(
                    text(f"INSERT INTO {TABLE} ({', '.join(keys)}) VALUES ({', '.join([':'+k for k in keys])})"),
                    params
                )
                count += 1
        db.session.commit()
        return jsonify({"count": count})
    except Exception as e:
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@bp.route(URL_BASE + '/export', methods=['GET'])
def export_rows():
    try:
        from openpyxl import Workbook
        cols = get_col_defs()
        wb = Workbook(); ws = wb.active; ws.title = 'Test Cases'
        ws.append([c.column_label for c in cols])
        for row in get_all_rows():
            ws.append([row.get(c.column_key, '') for c in cols])
        buf = io.BytesIO(); wb.save(buf); buf.seek(0)
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, download_name='testcases_export.xlsx')
    except Exception as e:
        return jsonify({"error": str(e)}), 500
