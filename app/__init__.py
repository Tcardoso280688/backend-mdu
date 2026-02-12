
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from .extensions import db
from .models import Usuario

bcrypt = Bcrypt()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # Configs
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'change-me-jwt')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mdu.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS (somente /api/*)
    origin = os.getenv('NETLIFY_ORIGIN', '*')
    CORS(app, resources={r"/api/*": {"origins": origin}}, supports_credentials=False)

    # Extensões
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Blueprints
    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.users import users_bp
    from .routes.logs import logs_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')

    @app.get('/health')
    def health():
        return jsonify(status='ok'), 200

    # Cria tabelas e admin padrão
    with app.app_context():
        db.create_all()
        seed_admin()

    return app


def seed_admin():
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@mdu.com')
    if not Usuario.query.filter_by(email=admin_email).first():
        from .models import Usuario
        from .utils import hash_password
        admin = Usuario(
            nome=os.getenv('ADMIN_NAME', 'Admin'),
            email=admin_email,
            senha_hash=hash_password(os.getenv('ADMIN_PASSWORD', '123456')),
            perfil=os.getenv('ADMIN_ROLE', 'admin')
        )
        db.session.add(admin)
        db.session.commit()
