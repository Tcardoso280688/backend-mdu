import os
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

    # Engine mais resiliente (pré-ping, reciclagem e SSL por garantia)
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {})
    app.config['SQLALCHEMY_ENGINE_OPTIONS'].update({
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'sslmode': 'require'}  # reforça o SSL mesmo já estando na URL
    })

    # CORS: libere apenas seu Netlify (ou * para teste)
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

    # ROTA TEMPORÁRIA de diagnóstico do banco (não deixa o boot cair)
    @app.get("/dbhealth")
    def dbhealth():
        try:
            db.session.execute(text("SELECT 1"))
            return jsonify(db="ok"), 200
        except Exception as e:
            # devolve a mensagem exata do Postgres/driver
            return jsonify(db="error", error=str(e)), 500

    # ------------------ Init do DB protegida ------------------
    with app.app_context():
        try:
            db.create_all()
            # só faz seed se o banco respondeu
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

    # evita duplicar
    if Usuario.query.filter_by(email=email).first():
        return

    nome = os.getenv('ADMIN_NAME', 'Admin')
    senha = os.getenv('ADMIN_PASSWORD', '123456')
    perfil = os.getenv('ADMIN_ROLE', 'admin')

    # ATENÇÃO: use o MESMO campo do seu models.py
    # - se o seu modelo tiver 'password_hash', troque a linha abaixo para 'password_hash=...'
    admin = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_password(senha)
    )

    # se o seu modelo tiver atributo 'perfil'
    try:
        admin.perfil = perfil
    except Exception:
        pass

    db.session.add(admin)
    db.session.commit()
