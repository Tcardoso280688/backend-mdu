import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Usuario
from ..utils import verify_password, hash_password

auth_bp = Blueprint("auth_bp", __name__)

def _get_user_hash(user):
    """
    Recupera o hash de senha do usuário, independente do nome do campo no model.
    Retorna None se não existir.
    """
    return getattr(user, "senha_hash", None) or getattr(user, "password_hash", None)

@auth_bp.post("/login")
def login():
    """
    Login robusto:
    - Nunca lança 500 por hash inválido/nulo
    - Responde 400 se faltar email/senha
    - Responde 401 para credenciais inválidas
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""
    if not email or not senha:
        return jsonify(message="Email e senha são obrigatórios"), 400

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify(message="Credenciais inválidas"), 401

    user_hash = _get_user_hash(user)
    try:
        if not user_hash or not verify_password(user_hash, senha):
            return jsonify(message="Credenciais inválidas"), 401
    except Exception as e:
        # Caso o hash seja inválido (ex.: texto plano antigo), não quebrar:
        current_app.logger.exception(f"Falha ao validar senha para {email}: {e}")
        return jsonify(message="Credenciais inválidas"), 401

    token = create_access_token(identity={
        "id": user.id,
        "email": user.email,
        "perfil": getattr(user, "perfil", "user"),
        "nome": user.nome
    })
    return jsonify(access_token=token, user={
        "id": user.id,
        "email": user.email,
        "perfil": getattr(user, "perfil", "user"),
        "nome": user.nome
    }), 200


@auth_bp.post("/reset-admin")
def reset_admin():
    """
    Rota de emergência/garantia do admin:
    - Protegida por token de ambiente ADMIN_RESET_TOKEN (querystring: ?token=...)
    - Recria (ou corrige) o admin com as variáveis ADMIN_*
    - NÃO manter em produção; use apenas para ajuste inicial e depois remova/disable.
    """
    token = request.args.get("token")
    expected = os.getenv("ADMIN_RESET_TOKEN")
    if not expected or token != expected:
        return jsonify(message="Forbidden"), 403

    email = (os.getenv("ADMIN_EMAIL", "admin@mdu.com") or "").strip().lower()
    nome = os.getenv("ADMIN_NAME", "Admin")
    senha = os.getenv("ADMIN_PASSWORD", "123456")
    perfil = os.getenv("ADMIN_ROLE", "admin")

    if not email:
        return jsonify(message="ADMIN_EMAIL não configurado"), 400

    try:
        user = Usuario.query.filter_by(email=email).first()
        if not user:
            # cria novo admin
            user = Usuario(nome=nome, email=email)

        # seta o hash no(s) campo(s) que existir(em) no model
        if hasattr(user, "senha_hash"):
            user.senha_hash = hash_password(senha)
        if hasattr(user, "password_hash"):
            user.password_hash = hash_password(senha)

        # seta perfil se o model tiver esse atributo
        if hasattr(user, "perfil"):
            user.perfil = perfil

        db.session.add(user)
        db.session.commit()
        return jsonify(message="Admin garantido/resetado com sucesso"), 200

    except SQLAlchemyError as e:
        current_app.logger.exception(f"Erro ao resetar admin: {e}")
        db.session.rollback()
        return jsonify(message="Erro ao resetar admin"), 500
