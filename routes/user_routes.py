# user_routes.py — User-facing routes Blueprint for ZTB Super App
from flask import Blueprint, request, jsonify, session, render_template, send_file  # flask imports
from models import db, UserResponse, Question, QuestionCategory, AssessmentConfig, ValueProp, Asset, TestCase, POVPlanner, Roadblock  # import models
import json  # import json for data handling
import io  # import io for in-memory file handling
from openpyxl import Workbook  # import openpyxl for Excel generation
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side  # import styles
from datetime import datetime  # import datetime for timestamps

user_bp = Blueprint('user', __name__, url_prefix='/user')  # create user blueprint

# ─────────────────────────────────────────────
# Assessment Session Routes
# ─────────────────────────────────────────────
@user_bp.route('/start', methods=['POST'])  # route to start a new assessment
def start_assessment():  # function to start assessment
    data = request.get_json()  # get JSON data from request
    customer_name = data.get('customer_name', '').strip()  # get customer name
    se_name = data.get('se_name', '').strip()  # get SE name
    if not customer_name or not se_name:  # validate required fields
        return jsonify({'error': 'Customer name and SE name are required'}), 400  # return error
    session['customer_name'] = customer_name  # store customer name in session
    session['se_name'] = se_name  # store SE name in session
    session['assessment_started'] = True  # mark assessment as started
    session['responses'] = {}  # initialize empty responses dict
    return jsonify({'success': True, 'message': 'Assessment started'})  # return success

@user_bp.route('/questions', methods=['GET'])  # route to get assessment questions
def get_questions():  # function to fetch questions
    config = AssessmentConfig.query.first()  # get assessment config
    if not config:  # if no config exists
        return jsonify({'error': 'Assessment not configured'}), 404  # return error
    categories = QuestionCategory.query.order_by(QuestionCategory.order_index).all()  # get ordered categories
    result = []  # initialize result list
    for cat in categories:  # loop through categories
        questions = Question.query.filter_by(  # get questions for this category
            category_id=cat.id, is_active=True  # filter active questions
        ).order_by(Question.order_index).all()  # order by index
        result.append({  # append category with questions
            'category_id': cat.id,  # category ID
            'category_name': cat.name,  # category name
            'questions': [q.to_dict() for q in questions]  # list of question dicts
        })
    return jsonify({'categories': result})  # return all categories with questions

@user_bp.route('/submit', methods=['POST'])  # route to submit assessment responses
def submit_responses():  # function to save responses
    if not session.get('assessment_started'):  # check if assessment is active
        return jsonify({'error': 'No active assessment session'}), 400  # return error
    data = request.get_json()  # get JSON data
    responses = data.get('responses', {})  # get responses dict
    customer_name = session.get('customer_name', '')  # get customer name from session
    se_name = session.get('se_name', '')  # get SE name from session
    user_response = UserResponse(  # create UserResponse record
        customer_name=customer_name,  # set customer name
        se_name=se_name,  # set SE name
        responses=json.dumps(responses),  # serialize responses to JSON
        submitted_at=datetime.utcnow()  # set submission timestamp
    )
    db.session.add(user_response)  # add to session
    db.session.commit()  # commit to database
    session['response_id'] = user_response.id  # store response ID in session
    return jsonify({'success': True, 'response_id': user_response.id})  # return success

@user_bp.route('/results/<int:response_id>', methods=['GET'])  # route to get assessment results
def get_results(response_id):  # function to get results
    response = UserResponse.query.get_or_404(response_id)  # get response by ID
    responses_dict = json.loads(response.responses)  # deserialize responses
    value_props = ValueProp.query.filter_by(is_active=True).all()  # get active value props
    matched = []  # initialize matched value props list
    for vp in value_props:  # loop through value props
        trigger_ids = json.loads(vp.trigger_question_ids) if vp.trigger_question_ids else []  # get trigger IDs
        if any(str(tid) in responses_dict for tid in trigger_ids):  # check if any trigger matches
            matched.append(vp.to_dict())  # add to matched list
    return jsonify({  # return results
        'customer_name': response.customer_name,  # customer name
        'se_name': response.se_name,  # SE name
        'submitted_at': response.submitted_at.isoformat(),  # submission time
        'matched_value_props': matched  # matched value propositions
    })

# ─────────────────────────────────────────────
# Excel Export Route
# ─────────────────────────────────────────────
@user_bp.route('/export/<int:response_id>', methods=['GET'])  # route to export results as Excel
def export_excel(response_id):  # function to generate Excel file
    response = UserResponse.query.get_or_404(response_id)  # get response by ID
    wb = Workbook()  # create new workbook
    ws = wb.active  # get active worksheet
    ws.title = 'ZTB Assessment Results'  # set worksheet title

    # --- Header styling ---
    header_font = Font(bold=True, color='FFFFFF', size=12)  # white bold font for headers
    header_fill = PatternFill(start_color='003366', end_color='003366', fill_type='solid')  # dark blue fill
    header_alignment = Alignment(horizontal='center', vertical='center')  # center alignment

    # --- Title row ---
    ws.merge_cells('A1:D1')  # merge cells for title
    ws['A1'] = 'ZTB Super App — Assessment Results'  # set title text
    ws['A1'].font = Font(bold=True, size=14, color='003366')  # style title
    ws['A1'].alignment = Alignment(horizontal='center')  # center title

    # --- Metadata rows ---
    ws['A3'] = 'Customer:'  # label
    ws['B3'] = response.customer_name  # value
    ws['A4'] = 'SE Name:'  # label
    ws['B4'] = response.se_name  # value
    ws['A5'] = 'Submitted:'  # label
    ws['B5'] = response.submitted_at.strftime('%Y-%m-%d %H:%M')  # formatted datetime

    # --- Column headers ---
    headers = ['#', 'Question', 'Response', 'Notes']  # column header labels
    for col_idx, header in enumerate(headers, 1):  # loop through headers
        cell = ws.cell(row=7, column=col_idx, value=header)  # write header
        cell.font = header_font  # apply font
        cell.fill = header_fill  # apply fill
        cell.alignment = header_alignment  # apply alignment

    # --- Data rows ---
    responses_dict = json.loads(response.responses)  # deserialize responses
    row = 8  # start data at row 8
    for q_id, answer in responses_dict.items():  # loop through responses
        question = Question.query.get(int(q_id))  # get question by ID
        ws.cell(row=row, column=1, value=row - 7)  # row number
        ws.cell(row=row, column=2, value=question.text if question else f'Q{q_id}')  # question text
        ws.cell(row=row, column=3, value=answer)  # answer
        ws.cell(row=row, column=4, value='')  # empty notes column
        row += 1  # increment row

    # --- Auto-size columns ---
    for col in ws.columns:  # loop through all columns
        max_len = max(len(str(cell.value or '')) for cell in col)  # find max content length
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)  # set width

    # --- Save to in-memory buffer ---
    buffer = io.BytesIO()  # create in-memory buffer
    wb.save(buffer)  # save workbook to buffer
    buffer.seek(0)  # rewind buffer to start

    filename = f"ZTB_Assessment_{response.customer_name.replace(' ', '_')}_{response.submitted_at.strftime('%Y%m%d')}.xlsx"  # dynamic filename
    return send_file(  # send file to client
        buffer,  # file buffer
        as_attachment=True,  # force download
        download_name=filename,  # set filename
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Excel MIME type
    )
