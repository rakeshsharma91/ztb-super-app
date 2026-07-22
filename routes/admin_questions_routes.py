# admin_questions_routes.py — Questions Library routes for ZTB Super App
from flask import Blueprint, request, jsonify, session  # flask imports
from models import db, Question, QuestionCategory  # import models
from functools import wraps  # import wraps for decorator
import json  # import json for data handling

admin_questions_bp = Blueprint('admin_questions', __name__, url_prefix='/admin/questions')  # create blueprint

# ─────────────────────────────────────────────
# Auth decorator
# ─────────────────────────────────────────────
def require_admin(f):  # decorator to protect admin routes
    @wraps(f)  # preserve function metadata
    def decorated(*args, **kwargs):  # wrapper function
        if not session.get('admin_logged_in'):  # check if admin is logged in
            return jsonify({'error': 'Unauthorized'}), 401  # return 401 if not
        return f(*args, **kwargs)  # call original function if authenticated
    return decorated  # return wrapper

# ─────────────────────────────────────────────
# GET /admin/questions/ — list all questions with optional filters
# ─────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['GET'])  # route for listing questions
@require_admin  # protect with auth decorator
def list_questions():  # function to list all questions
    category = request.args.get('category')  # optional category filter
    search = request.args.get('search', '')  # optional search term
    page = int(request.args.get('page', 1))  # page number, default 1
    per_page = int(request.args.get('per_page', 50))  # items per page, default 50

    query = Question.query  # start query
    if category:  # if category filter provided
        query = query.filter_by(category=category)  # filter by category
    if search:  # if search term provided
        query = query.filter(Question.question_text.ilike(f'%{search}%'))  # filter by search term

    total = query.count()  # total count for pagination
    questions = query.order_by(Question.category, Question.id).offset((page-1)*per_page).limit(per_page).all()  # paginated results

    return jsonify({  # return JSON response
        'questions': [q.to_dict() for q in questions],  # list of questions
        'total': total,  # total count
        'page': page,  # current page
        'per_page': per_page,  # items per page
        'pages': (total + per_page - 1) // per_page  # total pages
    }), 200  # HTTP 200 OK

# ─────────────────────────────────────────────
# POST /admin/questions/ — create a new question
# ─────────────────────────────────────────────
@admin_questions_bp.route('/', methods=['POST'])  # route for creating a question
@require_admin  # protect with auth decorator
def create_question():  # function to create a question
    data = request.get_json()  # get JSON data from request body
    if not data:  # if no data provided
        return jsonify({'error': 'No data provided'}), 400  # return 400 Bad Request

    question_text = data.get('question_text', '').strip()  # get question text
    category = data.get('category', '').strip()  # get category
    sub_category = data.get('sub_category', '').strip()  # get sub category
    answer_type = data.get('answer_type', 'text')  # get answer type (text/select/multi)
    options = data.get('options', [])  # get options for select/multi types
    is_required = data.get('is_required', True)  # get required flag
    order_index = data.get('order_index', 0)  # get display order

    if not question_text:  # validate question text
        return jsonify({'error': 'question_text is required'}), 400  # return error
    if not category:  # validate category
        return jsonify({'error': 'category is required'}), 400  # return error

    question = Question(  # create new Question instance
        question_text=question_text,  # set question text
        category=category,  # set category
        sub_category=sub_category,  # set sub category
        answer_type=answer_type,  # set answer type
        options=json.dumps(options) if options else None,  # serialize options to JSON
        is_required=is_required,  # set required flag
        order_index=order_index  # set display order
    )
    db.session.add(question)  # add to session
    db.session.commit()  # commit to database
    return jsonify({'message': 'Question created', 'question': question.to_dict()}), 201  # return 201 Created

# ─────────────────────────────────────────────
# GET /admin/questions/<id> — get a single question
# ─────────────────────────────────────────────
@admin_questions_bp.route('/<int:question_id>', methods=['GET'])  # route for single question
@require_admin  # protect with auth decorator
def get_question(question_id):  # function to get a question
    question = Question.query.get_or_404(question_id)  # get question or 404
    return jsonify(question.to_dict()), 200  # return question as JSON

# ─────────────────────────────────────────────
# PUT /admin/questions/<id> — update a question
# ─────────────────────────────────────────────
@admin_questions_bp.route('/<int:question_id>', methods=['PUT'])  # route for updating a question
@require_admin  # protect with auth decorator
def update_question(question_id):  # function to update a question
    question = Question.query.get_or_404(question_id)  # get question or 404
    data = request.get_json()  # get JSON data
    if not data:  # if no data
        return jsonify({'error': 'No data provided'}), 400  # return error

    if 'question_text' in data:  # if question_text in data
        question.question_text = data['question_text'].strip()  # update question text
    if 'category' in data:  # if category in data
        question.category = data['category'].strip()  # update category
    if 'sub_category' in data:  # if sub_category in data
        question.sub_category = data['sub_category'].strip()  # update sub category
    if 'answer_type' in data:  # if answer_type in data
        question.answer_type = data['answer_type']  # update answer type
    if 'options' in data:  # if options in data
        question.options = json.dumps(data['options']) if data['options'] else None  # update options
    if 'is_required' in data:  # if is_required in data
        question.is_required = data['is_required']  # update required flag
    if 'order_index' in data:  # if order_index in data
        question.order_index = data['order_index']  # update display order

    db.session.commit()  # commit changes
    return jsonify({'message': 'Question updated', 'question': question.to_dict()}), 200  # return updated question

# ─────────────────────────────────────────────
# DELETE /admin/questions/<id> — delete a question
# ─────────────────────────────────────────────
@admin_questions_bp.route('/<int:question_id>', methods=['DELETE'])  # route for deleting a question
@require_admin  # protect with auth decorator
def delete_question(question_id):  # function to delete a question
    question = Question.query.get_or_404(question_id)  # get question or 404
    db.session.delete(question)  # delete from session
    db.session.commit()  # commit to database
    return jsonify({'message': 'Question deleted'}), 200  # return success

# ─────────────────────────────────────────────
# GET /admin/questions/categories — list all categories
# ─────────────────────────────────────────────
@admin_questions_bp.route('/categories', methods=['GET'])  # route for listing categories
@require_admin  # protect with auth decorator
def list_categories():  # function to list categories
    categories = db.session.query(Question.category).distinct().order_by(Question.category).all()  # get distinct categories
    return jsonify({'categories': [c[0] for c in categories]}), 200  # return list of categories

# ─────────────────────────────────────────────
# POST /admin/questions/bulk — bulk import questions from JSON array
# ─────────────────────────────────────────────
@admin_questions_bp.route('/bulk', methods=['POST'])  # route for bulk import
@require_admin  # protect with auth decorator
def bulk_import():  # function for bulk import
    data = request.get_json()  # get JSON data
    if not data or not isinstance(data, list):  # validate it's a list
        return jsonify({'error': 'Expected a JSON array of questions'}), 400  # return error

    created = 0  # counter for created questions
    errors = []  # list for errors

    for i, item in enumerate(data):  # iterate over each item
        try:  # try to create each question
            q = Question(  # create Question instance
                question_text=item.get('question_text', '').strip(),  # set question text
                category=item.get('category', '').strip(),  # set category
                sub_category=item.get('sub_category', '').strip(),  # set sub category
                answer_type=item.get('answer_type', 'text'),  # set answer type
                options=json.dumps(item.get('options', [])) if item.get('options') else None,  # set options
                is_required=item.get('is_required', True),  # set required flag
                order_index=item.get('order_index', i)  # set display order
            )
            db.session.add(q)  # add to session
            created += 1  # increment counter
        except Exception as e:  # catch any errors
            errors.append({'index': i, 'error': str(e)})  # log error

    db.session.commit()  # commit all at once
    return jsonify({'created': created, 'errors': errors}), 201  # return summary
