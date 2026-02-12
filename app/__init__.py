import os
from flask import Flask, jsonify
from .extensions import db
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

def create_app():
    app = Flask(__name__)

    # exemplo: configs/inits
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    # db.init_app(app)
    # CORS(app, resources={r"/api/*": {"origins": os.getenv("NETLIFY_ORIGIN", "*")}})

    # blueprints
    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.users import users_bp
    from .routes.logs import logs_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(logs_bp, url_prefix="/api/logs")

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    return app
