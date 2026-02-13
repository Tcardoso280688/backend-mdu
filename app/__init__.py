import os
import re
from urllib.parse import urlparse

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from .extensions import db
from .utils import hash_password
from .models import Usuario

jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # ------------------ Configs essenciais ------------------
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'troque-esta-chave')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'troque-esta-chave-jwt')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mdu.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Engine mais resiliente (pré-ping, reciclagem e SSL)
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
    app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'require'}  # reforça SSL mesmo já estando na URL
    })

    # CORS: libere o seu domínio do Netlify
    CORS(app, resources={r"/api/*": {"origins": os.getenv("NETLIFY_ORIGIN", "*")}})

    # ------------------ Extensões ------------------
    db.init_app(app)
    jwt.init_app(app)

    # ------------------ Blueprints ------------------
    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.users import users_bp
    from .routes.logs import logs_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(logs_bp, url_prefix="/api/logs")

    # ------------------ Healthchecks ------------------
    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    # ROTA TEMPORÁRIA de diagnóstico do banco (não derruba o boot)
    @app.get("/dbhealth")
    def dbhealth():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify(db="ok"), 200
        except Exception as e:
            return jsonify(db="error", error=str(e)), 500

    # ROTA TEMPORÁRIA para ver o que a app está lendo de DATABASE_URL
    @app.get("/cfg")
    def cfg():
        url = os.getenv("DATABASE_URL", "")
        masked = re.sub(r":([^:@/\?]+)@", r":********@", url)
        try:
            p = urlparse(url)
            who = p.username or ""
            host = p.hostname or ""
            return jsonify(
                database_url=masked,
                parsed_username=who,
                parsed_host=host
            ), 200
        except Exception as e:
            return jsonify(database_url=masked, error=str(e)), 200

    # ------------------ Init do DB protegida ------------------
    with app.app_context():
        try:
            db.create_all()
            # só tenta seed se o banco respondeu
            db.session.execute(text("SELECT 1"))
            _seed_admin()
        except Exception as e:
            app.logger.exception(f"DB init failed: {e}")

    return app


def _seed_admin():
    """Cria um usuário admin a partir das variáveis de ambiente, se não existir."""
    email = (os.getenv('ADMIN_EMAIL', 'admin@mdu.com') or '').strip().lower()
    if not email:
        return

    # Evita duplicar
    if Usuario.query.filter_by(email=email).first():
        return

    nome = os.getenv('ADMIN_NAME', 'Admin')
    senha = os.getenv('ADMIN_PASSWORD', '123456')
    perfil = os.getenv('ADMIN_ROLE', 'admin')

    admin = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha)
    )
    # atribui perfil se existir no modelo
    try:
        admin.perfil = perfil
    except Exception:
        pass

    db.session.add(admin)
    db.session.commit()
