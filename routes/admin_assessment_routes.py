# admin_assessment_routes.py — Assessment configuration routes for ZTB Super App
from flask import Blueprint, request, jsonify, session  # flask imports
from models import db, AssessmentConfig, Question, QuestionCategory  # import models
from functools import wraps  # import wraps for decorator
import json  # import json for data handling

admin_assessment_bp = Blueprint('admin_assessment', __name__, url_prefix='/admin/assessment')  # create blueprint

# ─────────────────────────────────────────────
# Auth decorator
# ─────────────────────────────────────────────
def require_admin(f):  # decorator to protect admin routes
    @wraps(f)  # preserve function metadata
    def decorated(*args, **kwargs):  # wrapper function
        if not session.get('admin_logged_in'):  # check if admin is logged in
            return jsonify({'error': 'Unauthorized'}), 401  # return 401 if not
        return f(*args, **kwargs)  # call original function if authenticated
    return decorated  # return wrapped function

# ─────────────────────────────────────────────
# GET /admin/assessment/config — get assessment configuration
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/config', methods=['GET'])  # route for getting assessment config
@require_admin  # protect with auth decorator
def get_assessment_config():  # handler function
    configs = AssessmentConfig.query.all()  # fetch all config records
    return jsonify([c.to_dict() for c in configs])  # return as JSON list

# ─────────────────────────────────────────────
# POST /admin/assessment/config — save assessment configuration
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/config', methods=['POST'])  # route for saving config
@require_admin  # protect with auth decorator
def save_assessment_config():  # handler function
    data = request.get_json()  # parse JSON body
    if not data:  # validate input
        return jsonify({'error': 'No data provided'}), 400  # return 400 if empty

    key = data.get('key')  # get config key
    value = data.get('value')  # get config value

    if not key:  # validate key
        return jsonify({'error': 'Key is required'}), 400  # return 400 if missing

    existing = AssessmentConfig.query.filter_by(key=key).first()  # check if key exists
    if existing:  # if key exists
        existing.value = str(value)  # update value
        existing.updated_at = db.func.now()  # update timestamp
    else:  # if key doesn't exist
        new_config = AssessmentConfig(key=key, value=str(value))  # create new record
        db.session.add(new_config)  # add to session

    db.session.commit()  # commit to database
    return jsonify({'success': True, 'key': key, 'value': value})  # return success

# ─────────────────────────────────────────────
# GET /admin/assessment/questions — get questions available for assessment
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/questions', methods=['GET'])  # route for listing questions
@require_admin  # protect with auth decorator
def list_assessment_questions():  # handler function
    category = request.args.get('category')  # get optional category filter
    active_only = request.args.get('active', 'true').lower() == 'true'  # get active filter

    query = Question.query  # start base query

    if category:  # filter by category if provided
        query = query.filter(Question.category == category)  # apply category filter

    if active_only:  # filter to active questions only
        query = query.filter(Question.is_active == True)  # apply active filter

    questions = query.order_by(Question.category, Question.order_index).all()  # fetch ordered questions

    return jsonify([q.to_dict() for q in questions])  # return as JSON list

# ─────────────────────────────────────────────
# GET /admin/assessment/categories — get all question categories
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/categories', methods=['GET'])  # route for listing categories
@require_admin  # protect with auth decorator
def list_categories():  # handler function
    categories = QuestionCategory.query.order_by(QuestionCategory.order_index).all()  # fetch all categories
    return jsonify([c.to_dict() for c in categories])  # return as JSON list

# ─────────────────────────────────────────────
# POST /admin/assessment/categories — create a new category
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/categories', methods=['POST'])  # route for creating category
@require_admin  # protect with auth decorator
def create_category():  # handler function
    data = request.get_json()  # parse JSON body
    if not data or not data.get('name'):  # validate required field
        return jsonify({'error': 'Category name is required'}), 400  # return 400 if missing

    existing = QuestionCategory.query.filter_by(name=data['name']).first()  # check for duplicate
    if existing:  # if duplicate found
        return jsonify({'error': 'Category already exists'}), 409  # return 409 conflict

    max_order = db.session.query(db.func.max(QuestionCategory.order_index)).scalar() or 0  # get max order
    category = QuestionCategory(  # create new category
        name=data['name'],  # set name
        description=data.get('description', ''),  # set description
        order_index=max_order + 1  # set order after last
    )
    db.session.add(category)  # add to session
    db.session.commit()  # commit to database
    return jsonify(category.to_dict()), 201  # return created category

# ─────────────────────────────────────────────
# PUT /admin/assessment/categories/<id> — update a category
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/categories/<int:category_id>', methods=['PUT'])  # route for updating category
@require_admin  # protect with auth decorator
def update_category(category_id):  # handler function
    category = QuestionCategory.query.get_or_404(category_id)  # fetch category or 404
    data = request.get_json()  # parse JSON body

    if 'name' in data:  # update name if provided
        category.name = data['name']  # set new name
    if 'description' in data:  # update description if provided
        category.description = data['description']  # set new description
    if 'order_index' in data:  # update order if provided
        category.order_index = data['order_index']  # set new order

    db.session.commit()  # commit to database
    return jsonify(category.to_dict())  # return updated category

# ─────────────────────────────────────────────
# DELETE /admin/assessment/categories/<id> — delete a category
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/categories/<int:category_id>', methods=['DELETE'])  # route for deleting category
@require_admin  # protect with auth decorator
def delete_category(category_id):  # handler function
    category = QuestionCategory.query.get_or_404(category_id)  # fetch category or 404
    db.session.delete(category)  # delete from session
    db.session.commit()  # commit to database
    return jsonify({'success': True, 'deleted_id': category_id})  # return success

# ─────────────────────────────────────────────
# GET /admin/assessment/stats — get assessment statistics
# ─────────────────────────────────────────────
@admin_assessment_bp.route('/stats', methods=['GET'])  # route for stats
@require_admin  # protect with auth decorator
def get_assessment_stats():  # handler function
    from models import UserResponse  # import UserResponse model
    total_responses = UserResponse.query.count()  # count total responses
    total_questions = Question.query.filter_by(is_active=True).count()  # count active questions
    total_categories = QuestionCategory.query.count()  # count categories

    return jsonify({  # return stats dict
        'total_responses': total_responses,  # total user responses
        'total_questions': total_questions,  # total active questions
        'total_categories': total_categories,  # total categories
    })  # end stats dict
