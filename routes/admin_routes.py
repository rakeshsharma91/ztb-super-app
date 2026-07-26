# admin_routes.py — Admin routes Blueprint for ZTB Super App
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for  # flask imports
from werkzeug.security import check_password_hash, generate_password_hash  # password hashing
from models import db, AdminConfig, UserResponse, ColumnDefinition, ValueProp, Asset, TestCase, POVPlanner, Roadblock  # import all models
from functools import wraps  # import wraps for decorator
import json  # import json for data handling

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')  # create admin blueprint

# ─────────────────────────────────────────────
# Auth decorator
# ─────────────────────────────────────────────
def require_admin(f):  # decorator to protect admin routes
    @wraps(f)  # preserve function metadata
    def decorated(*args, **kwargs):  # wrapper function
        if not session.get('admin_logged_in'):  # check if admin is logged in
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401  # return 401 if not
        return f(*args, **kwargs)  # call original function if authorized
    return decorated  # return wrapper

# ─────────────────────────────────────────────
# Page Routes
# ─────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET'])  # admin login page
def login_page():  # render login page
    if session.get('admin_logged_in'):  # if already logged in
        return redirect(url_for('admin.dashboard'))  # redirect to dashboard
    return render_template('admin_login.html')  # render login template

@admin_bp.route('/dashboard', methods=['GET'])  # admin dashboard page
def dashboard():  # render dashboard
    if not session.get('admin_logged_in'):  # check auth
        return redirect(url_for('admin.login_page'))  # redirect to login if not authed
    return render_template('admin_dashboard.html')  # render dashboard template

@admin_bp.route('/logout', methods=['GET'])  # logout route
def logout():  # clear session and redirect
    session.clear()  # clear all session data
    return redirect(url_for('admin.login_page'))  # redirect to login page

# ─────────────────────────────────────────────
# Auth API Routes
# ─────────────────────────────────────────────
@admin_bp.route('/login', methods=['POST'])  # login POST handler
def login():  # handle login form submission
    data = request.get_json()  # get JSON body
    password = data.get('password', '')  # extract password from body
    config = AdminConfig.query.filter_by(key='admin_password').first()  # get stored password hash
    if config and check_password_hash(config.value, password):  # verify password
        session['admin_logged_in'] = True  # set session flag
        return jsonify({'success': True})  # return success
    return jsonify({'success': False, 'error': 'Invalid password'}), 401  # return error

@admin_bp.route('/change-password', methods=['POST'])  # change password route
@require_admin  # require admin auth
def change_password():  # handle password change
    data = request.get_json()  # get JSON body
    current = data.get('current_password', '')  # get current password
    new_pass = data.get('new_password', '')  # get new password
    config = AdminConfig.query.filter_by(key='admin_password').first()  # get stored hash
    if not config or not check_password_hash(config.value, current):  # verify current password
        return jsonify({'success': False, 'error': 'Current password incorrect'}), 400  # return error
    config.value = generate_password_hash(new_pass)  # hash new password
    db.session.commit()  # save to database
    return jsonify({'success': True})  # return success

# ─────────────────────────────────────────────
# Responses Routes
# ─────────────────────────────────────────────
@admin_bp.route('/responses', methods=['GET'])  # get all user responses
@require_admin  # require admin auth
def get_responses():  # return all responses
    return render_template('admin_responses.html')

@admin_bp.route('/responses/data', methods=['GET'])  # JSON API for responses data
@require_admin  # require admin auth
def get_responses_data():  # return all responses as JSON
    responses = UserResponse.query.order_by(UserResponse.created_at.desc()).all()
    return jsonify({'success': True, 'responses': [r.to_dict() for r in responses]})

@admin_bp.route('/responses/<int:response_id>', methods=['GET'])  # get single response
@require_admin  # require admin auth
def get_response(response_id):  # return one response by ID
    r = UserResponse.query.get_or_404(response_id)  # get response or 404
    return jsonify({'success': True, 'response': r.to_dict()})  # return as JSON

@admin_bp.route('/responses/<int:response_id>', methods=['DELETE'])  # delete a response
@require_admin  # require admin auth
def delete_response(response_id):  # delete one response by ID
    r = UserResponse.query.get_or_404(response_id)  # get response or 404
    db.session.delete(r)  # delete from session
    db.session.commit()  # commit to database
    return jsonify({'success': True})  # return success

# ─────────────────────────────────────────────
# Dynamic Columns Routes
# ─────────────────────────────────────────────
@admin_bp.route('/columns/<table_name>', methods=['GET'])  # get columns for a table
@require_admin  # require admin auth
def get_columns(table_name):  # return column definitions for a table
    cols = ColumnDefinition.query.filter_by(table_name=table_name).order_by(ColumnDefinition.display_order).all()  # query columns
    return jsonify({'success': True, 'columns': [c.to_dict() for c in cols]})  # return as JSON

@admin_bp.route('/columns/<table_name>', methods=['POST'])  # add a column
@require_admin  # require admin auth
def add_column(table_name):  # create a new column definition
    data = request.get_json()  # get JSON body
    max_order = db.session.query(db.func.max(ColumnDefinition.display_order)).filter_by(table_name=table_name).scalar() or 0  # get current max order
    col = ColumnDefinition(  # create new column
        table_name=table_name,  # set table name
        column_key=data['column_key'],  # set column key
        column_label=data['column_label'],  # set display label
        column_type=data.get('column_type', 'text'),  # set type (default text)
        is_required=data.get('is_required', False),  # set required flag
        is_system=False,  # user-created columns are not system columns
        display_order=max_order + 1  # set display order
    )
    db.session.add(col)  # add to session
    db.session.commit()  # commit to database
    return jsonify({'success': True, 'column': col.to_dict()})  # return created column

@admin_bp.route('/columns/<int:col_id>', methods=['PUT'])  # update a column
@require_admin  # require admin auth
def update_column(col_id):  # update column definition
    col = ColumnDefinition.query.get_or_404(col_id)  # get column or 404
    data = request.get_json()  # get JSON body
    col.column_label = data.get('column_label', col.column_label)  # update label
    col.column_type = data.get('column_type', col.column_type)  # update type
    col.is_required = data.get('is_required', col.is_required)  # update required flag
    db.session.commit()  # commit changes
    return jsonify({'success': True, 'column': col.to_dict()})  # return updated column

@admin_bp.route('/columns/<int:col_id>', methods=['DELETE'])  # delete a column
@require_admin  # require admin auth
def delete_column(col_id):  # delete column definition
    col = ColumnDefinition.query.get_or_404(col_id)  # get column or 404
    if col.is_system:  # cannot delete system columns
        return jsonify({'success': False, 'error': 'Cannot delete system columns'}), 400  # return error
    db.session.delete(col)  # delete from session
    db.session.commit()  # commit to database
    return jsonify({'success': True})  # return success

# Assets Library (B)
# ─────────────────────────────────────────────
@admin_bp.route('/assets', methods=['GET'])  # get all assets
@require_admin  # require admin auth
def get_assets():  # return all assets
    items = Asset.query.order_by(Asset.id).all()  # get all
    return jsonify({'success': True, 'items': [i.to_dict() for i in items]})  # return as JSON

@admin_bp.route('/assets', methods=['POST'])  # create asset
@require_admin  # require admin auth
def create_asset():  # create new asset
    data = request.get_json()  # get JSON body
    item = Asset(  # create new instance
        asset_name=data.get('asset_name', ''),  # asset name
        asset_type=data.get('asset_type', ''),  # asset type
        asset_url=data.get('asset_url', ''),  # asset URL
        description=data.get('description', ''),  # description
        extra_data=data.get('extra_data', {})  # extra dynamic columns
    )
    db.session.add(item)  # add to session
    db.session.commit()  # commit to database
    return jsonify({'success': True, 'item': item.to_dict()})  # return created item

@admin_bp.route('/assets/<int:item_id>', methods=['PUT'])  # update asset
@require_admin  # require admin auth
def update_asset(item_id):  # update existing asset
    item = Asset.query.get_or_404(item_id)  # get or 404
    data = request.get_json()  # get JSON body
    item.asset_name = data.get('asset_name', item.asset_name)  # update name
    item.asset_type = data.get('asset_type', item.asset_type)  # update type
    item.asset_url = data.get('asset_url', item.asset_url)  # update URL
    item.description = data.get('description', item.description)  # update description
    item.extra_data = data.get('extra_data', item.extra_data)  # update extra data
    db.session.commit()  # commit changes
    return jsonify({'success': True, 'item': item.to_dict()})  # return updated item

@admin_bp.route('/assets/<int:item_id>', methods=['DELETE'])  # delete asset
@require_admin  # require admin auth
def delete_asset(item_id):  # delete asset
    item = Asset.query.get_or_404(item_id)  # get or 404
    db.session.delete(item)  # delete
    db.session.commit()  # commit
    return jsonify({'success': True})  # return success

# ─────────────────────────────────────────────
# Test Cases Library (C)
# ─────────────────────────────────────────────
@admin_bp.route('/testcases', methods=['GET'])  # get all test cases
@require_admin  # require admin auth
def get_testcases():  # return all test cases
    items = TestCase.query.order_by(TestCase.id).all()  # get all
    return jsonify({'success': True, 'items': [i.to_dict() for i in items]})  # return as JSON

@admin_bp.route('/testcases', methods=['POST'])  # create test case
@require_admin  # require admin auth
def create_testcase():  # create new test case
    data = request.get_json()  # get JSON body
    item = TestCase(  # create new instance
        test_name=data.get('test_name', ''),  # test name
        test_category=data.get('test_category', ''),  # category
        test_description=data.get('test_description', ''),  # description
        expected_outcome=data.get('expected_outcome', ''),  # expected outcome
        extra_data=data.get('extra_data', {})  # extra dynamic columns
    )
    db.session.add(item)  # add to session
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return created

@admin_bp.route('/testcases/<int:item_id>', methods=['PUT'])  # update test case
@require_admin  # require admin auth
def update_testcase(item_id):  # update existing test case
    item = TestCase.query.get_or_404(item_id)  # get or 404
    data = request.get_json()  # get JSON body
    item.test_name = data.get('test_name', item.test_name)  # update name
    item.test_category = data.get('test_category', item.test_category)  # update category
    item.test_description = data.get('test_description', item.test_description)  # update description
    item.expected_outcome = data.get('expected_outcome', item.expected_outcome)  # update expected outcome
    item.extra_data = data.get('extra_data', item.extra_data)  # update extra data
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return updated

@admin_bp.route('/testcases/<int:item_id>', methods=['DELETE'])  # delete test case
@require_admin  # require admin auth
def delete_testcase(item_id):  # delete test case
    item = TestCase.query.get_or_404(item_id)  # get or 404
    db.session.delete(item)  # delete
    db.session.commit()  # commit
    return jsonify({'success': True})  # return success

# ─────────────────────────────────────────────
# POV Planner Library (D)
# ─────────────────────────────────────────────
@admin_bp.route('/povplanners', methods=['GET'])  # get all POV planners
@require_admin  # require admin auth
def get_povplanners():  # return all POV planners
    items = POVPlanner.query.order_by(POVPlanner.id).all()  # get all
    return jsonify({'success': True, 'items': [i.to_dict() for i in items]})  # return as JSON

@admin_bp.route('/povplanners', methods=['POST'])  # create POV planner
@require_admin  # require admin auth
def create_povplanner():  # create new POV planner entry
    data = request.get_json()  # get JSON body
    item = POVPlanner(  # create new instance
        activity=data.get('activity', ''),  # activity name
        owner=data.get('owner', ''),  # owner
        timeline=data.get('timeline', ''),  # timeline
        status=data.get('status', ''),  # status
        notes=data.get('notes', ''),  # notes
        extra_data=data.get('extra_data', {})  # extra dynamic columns
    )
    db.session.add(item)  # add to session
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return created

@admin_bp.route('/povplanners/<int:item_id>', methods=['PUT'])  # update POV planner
@require_admin  # require admin auth
def update_povplanner(item_id):  # update existing POV planner
    item = POVPlanner.query.get_or_404(item_id)  # get or 404
    data = request.get_json()  # get JSON body
    item.activity = data.get('activity', item.activity)  # update activity
    item.owner = data.get('owner', item.owner)  # update owner
    item.timeline = data.get('timeline', item.timeline)  # update timeline
    item.status = data.get('status', item.status)  # update status
    item.notes = data.get('notes', item.notes)  # update notes
    item.extra_data = data.get('extra_data', item.extra_data)  # update extra data
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return updated

@admin_bp.route('/povplanners/<int:item_id>', methods=['DELETE'])  # delete POV planner
@require_admin  # require admin auth
def delete_povplanner(item_id):  # delete POV planner entry
    item = POVPlanner.query.get_or_404(item_id)  # get or 404
    db.session.delete(item)  # delete
    db.session.commit()  # commit
    return jsonify({'success': True})  # return success

# ─────────────────────────────────────────────
# Roadblocks Library (E)
# ─────────────────────────────────────────────
@admin_bp.route('/roadblocks', methods=['GET'])  # get all roadblocks
@require_admin  # require admin auth
def get_roadblocks():  # return all roadblocks
    items = Roadblock.query.order_by(Roadblock.id).all()  # get all
    return jsonify({'success': True, 'items': [i.to_dict() for i in items]})  # return as JSON

@admin_bp.route('/roadblocks', methods=['POST'])  # create roadblock
@require_admin  # require admin auth
def create_roadblock():  # create new roadblock
    data = request.get_json()  # get JSON body
    item = Roadblock(  # create new instance
        roadblock_name=data.get('roadblock_name', ''),  # roadblock name
        category=data.get('category', ''),  # category
        description=data.get('description', ''),  # description
        mitigation=data.get('mitigation', ''),  # mitigation strategy
        extra_data=data.get('extra_data', {})  # extra dynamic columns
    )
    db.session.add(item)  # add to session
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return created

@admin_bp.route('/roadblocks/<int:item_id>', methods=['PUT'])  # update roadblock
@require_admin  # require admin auth
def update_roadblock(item_id):  # update existing roadblock
    item = Roadblock.query.get_or_404(item_id)  # get or 404
    data = request.get_json()  # get JSON body
    item.roadblock_name = data.get('roadblock_name', item.roadblock_name)  # update name
    item.category = data.get('category', item.category)  # update category
    item.description = data.get('description', item.description)  # update description
    item.mitigation = data.get('mitigation', item.mitigation)  # update mitigation
    item.extra_data = data.get('extra_data', item.extra_data)  # update extra data
    db.session.commit()  # commit
    return jsonify({'success': True, 'item': item.to_dict()})  # return updated

@admin_bp.route('/roadblocks/<int:item_id>', methods=['DELETE'])  # delete roadblock
@require_admin  # require admin auth
def delete_roadblock(item_id):  # delete roadblock
    item = Roadblock.query.get_or_404(item_id)  # get or 404
    db.session.delete(item)  # delete
    db.session.commit()  # commit
    return jsonify({'success': True})  # return success
