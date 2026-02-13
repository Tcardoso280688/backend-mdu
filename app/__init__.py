import os
from flask import Flask, jsonify
from .extensions import db
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# se você usa bcrypt em utils.py:
from .utils import hash_password
from .models import Usuario

jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Configurações essenciais
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'troque-esta-chave')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'troque-esta-chave-jwt')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mdu.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # CORS: libere apenas seu Netlify
    CORS(app, resources={r"/api/*": {"origins": os.getenv("NETLIFY_ORIGIN", "*")}})

    # Inicia extensões
    db.init_app(app)
    jwt.init_app(app)

    # Registra rotas (blueprints)
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

    # >>> Cria tabelas e ADMIN na subida <<<
    with app.app_context():
        db.create_all()
        _seed_admin()

    return app


def _seed_admin():
    """Cria um usuário admin a partir das variáveis de ambiente, se não existir."""
    email = os.getenv('ADMIN_EMAIL', 'admin@mdu.com').strip().lower()
    if not email:
        return
    # evita duplicar
    if Usuario.query.filter_by(email=email).first():
        return

    nome = os.getenv('ADMIN_NAME', 'Admin')
    senha = os.getenv('ADMIN_PASSWORD', '123456')
    perfil = os.getenv('ADMIN_ROLE', 'admin')

    admin = Usuario(
        nome=nome,
        email=email,
        # Atenção: use o MESMO campo do seu models.py (senha_hash ou password_hash)
        senha_hash=hash_password(senha),   # se no seu models for password_hash, troque aqui.
        perfil=perfil
    )
    db.session.add(admin)
    db.session.commit()
