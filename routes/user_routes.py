# user_routes.py — Complete User-Facing Routes for ZTB Super App
from flask import Blueprint, request, jsonify, session, render_template, send_file
from models import (db, UserResponse, Question, QuestionOption,
                    AssessmentConfig, QuestionCategory,
                    ValueProp, Asset, TestCase, POVPlanner, Roadblock,
                    ColumnDefinition)
import json, io
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

def _hdr(cell, text, bg='003366', fg='FFFFFF', sz=11, bold=True):
    cell.value = text
    cell.font = Font(bold=bold, color=fg, size=sz)
    cell.fill = PatternFill(start_color=bg, end_color=bg, fill_type='solid')
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

def _thin_border():
    s = Side(style='thin', color='CCCCCC')
    return Border(left=s, right=s, top=s, bottom=s)

def _autosize(ws, max_width=60):
    for col in ws.columns:
        best = 10
        for cell in col:
            try:
                best = max(best, len(str(cell.value or '')))
            except Exception:
                pass
        ws.column_dimensions[col[0].column_letter].width = min(best + 4, max_width)

def _collect(model, triggered_ids):
    from sqlalchemy import text
    table_name = model.__tablename__

    # Check if mandatory column exists in the actual DB table
    with db.engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = :tname AND column_name = 'mandatory'
        """), {"tname": table_name})
        has_mandatory = result.fetchone() is not None

    if has_mandatory:
        with db.engine.connect() as conn:
            rows = conn.execute(
                text(f"SELECT id FROM {table_name} WHERE mandatory = TRUE")
            ).fetchall()
        mandatory_ids = {row[0] for row in rows}
        all_rows = {row[0]: model.query.get(row[0]) for row in rows}
    else:
        mandatory_ids = set()
        all_rows = {}

    for rid in triggered_ids:
        if rid not in mandatory_ids:
            obj = model.query.get(rid)
            if obj:
                all_rows[rid] = obj

    return list(all_rows.values())

def _get_col_defs(table_name):
    return ColumnDefinition.query.filter_by(table_name=table_name)\
        .order_by(ColumnDefinition.display_order).all()

@user_bp.route('/')
def landing():
    return render_template('user_landing.html')

@user_bp.route('/start', methods=['POST'])
def start_assessment():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    customer_name = (data.get('customer_name') or '').strip()
    se_name = (data.get('se_name') or '').strip()
    if not customer_name:
        return jsonify({'error': 'Customer name is required'}), 400
    session['customer_name'] = customer_name
    session['se_name'] = se_name
    session['assessment_started'] = True
    session['responses'] = {}
    return jsonify({'success': True, 'message': 'Assessment started'})

@user_bp.route('/questions', methods=['GET'])
def get_questions():
    # Load all questions sorted globally by order
    all_questions = Question.query.order_by(Question.order).all()
    result = []
    for q in all_questions:
        cat = QuestionCategory.query.get(q.category_id)
        opts = []
        for o in sorted(q.options, key=lambda x: x.id):
            opts.append({'id': o.id, 'label': o.label})
        result.append({
            'question_id':  q.id,
            'category':     cat.name if cat else '',
            'text':         q.text,
            'options_type': q.options_type,
            'info_only':    q.info_only,
            'options':      opts
        })
    return render_template('user_assessment.html', questions=result)

@user_bp.route('/submit', methods=['POST'])
def submit_responses():
    data = request.get_json()
    responses = data.get('responses', {})
    customer_name = session.get('customer_name') or data.get('customer_name', 'Unknown')
    se_name       = session.get('se_name')        or data.get('se_name', '')
    vp_ids    = set()
    asset_ids = set()
    tc_ids    = set()
    rb_ids    = set()
    pov_ids   = set()
    for q_id_str, value in responses.items():
        try:
            q_id = int(q_id_str)
        except (ValueError, TypeError):
            continue
        question = Question.query.get(q_id)
        if not question or question.info_only:
            continue
        selected_option_ids = []
        if question.options_type == 'select_all':
            if isinstance(value, list):
                selected_option_ids = [int(v) for v in value if str(v).isdigit()]
        elif question.options_type == 'select_one':
            if value and str(value).isdigit():
                selected_option_ids = [int(value)]
        for opt_id in selected_option_ids:
            opt = QuestionOption.query.get(opt_id)
            if not opt:
                continue
    user_response = UserResponse(
        customer_name=customer_name,
        se_name=se_name,
        answers=responses,
        completed_at=datetime.utcnow()
    )
    db.session.add(user_response)
    db.session.commit()
    session['response_id'] = user_response.id
    return jsonify({
        'success':     True,
        'response_id': user_response.id
    })

@user_bp.route('/export', methods=['GET'])
def export_excel():
    customer_name = session.get('customer_name', 'Customer')
    se_name       = session.get('se_name', '')
    vp_ids        = session.get('vp_ids',    [])
    asset_ids     = session.get('asset_ids', [])
    tc_ids        = session.get('tc_ids',    [])
    rb_ids        = session.get('rb_ids',    [])
    pov_ids       = session.get('pov_ids',   [])
    vp_rows    = _collect(ValueProp,  vp_ids)
    asset_rows = _collect(Asset,      asset_ids)
    tc_rows    = _collect(TestCase,   tc_ids)
    rb_rows    = _collect(Roadblock,  rb_ids)
    pov_rows   = _collect(POVPlanner, pov_ids)
    wb = Workbook()

    ws_a = wb.active
    ws_a.title = 'Assessment'
    _hdr(ws_a['A1'], 'Customer Name')
    ws_a['B1'] = customer_name
    ws_a.column_dimensions['A'].width = 22
    ws_a.column_dimensions['B'].width = 40

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    safe_name = customer_name.replace(' ', '-').replace('/', '-')
    filename  = f"{safe_name}-ztb.xlsx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
