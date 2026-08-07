import os
from flask import Flask
from models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    """App factory — used by init_db.py and gunicorn."""
    app = Flask(__name__)

    # Load config
    from config import config
    app.config.from_object(config)

    # Init db
    db.init_app(app)

    # Register blueprints
    from routes.admin_routes import admin_bp
    from routes.admin_questions_routes import admin_questions_bp
    from routes.admin_assessment_routes import admin_assessment_bp
    from routes.user_routes import user_bp
    from routes.admin_valueprops_routes import bp as valueprops_bp
    from routes.admin_assets_routes import bp as assets_bp
    from routes.admin_testcases_routes import bp as testcases_bp
    from routes.admin_povplanner_routes import bp as povplanner_bp
    from routes.admin_roadblocks_routes import bp as roadblocks_bp
    from routes.admin_responses_routes import responses_bp
    from routes.admin_sections_routes import sections_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_questions_bp)
    app.register_blueprint(admin_assessment_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(valueprops_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(testcases_bp)
    app.register_blueprint(povplanner_bp)
    app.register_blueprint(roadblocks_bp)
    app.register_blueprint(responses_bp)
    app.register_blueprint(sections_bp)

    return app

# Create app instance for direct use (init_sample_data.py, gunicorn)
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
