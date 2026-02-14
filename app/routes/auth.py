from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from sqlalchemy.exc import SQLAlchemyError

from ..extensions import db
from ..models import Usuario
from ..utils import verify_password, hash_password
import os

auth_bp = Blueprint("auth_bp", __name__)

def _get_user_hash(user):
    return getattr(user, "senha_hash", None) or getattr(user, "password_hash", None)

@auth_bp.post("/login")
def login():
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
        current_app.logger.exception(f"Falha ao validar senha para {email}: {e}")
        return jsonify(message="Credenciais inválidas"), 401

    # >>>>>>>>>>>>>>> ALTERAÇÃO AQUI <<<<<<<<<<<<<<<
    # identity precisa ser STRING. Envie outros dados em additional_claims.
    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "email": user.email,
            "perfil": getattr(user, "perfil", "user"),
            "nome": user.nome
        }
    )

    return jsonify(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "perfil": getattr(user, "perfil", "user"),
            "nome": user.nome
        }
    ), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    # Agora get_jwt_identity() retorna apenas o ID (string)
    uid = get_jwt_identity()
    claims = get_jwt()  # contém email, perfil, nome (additional_claims)
    return jsonify(user={
        "id": uid,
        "email": claims.get("email"),
        "perfil": claims.get("perfil"),
        "nome": claims.get("nome")
    }), 200


@auth_bp.post("/reset-admin")
def reset_admin():
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
            user = Usuario(nome=nome, email=email)

        if hasattr(user, "senha_hash"):
            user.senha_hash = hash_password(senha)
        if hasattr(user, "password_hash"):
            user.password_hash = hash_password(senha)

        if hasattr(user, "perfil"):
            user.perfil = perfil

        db.session.add(user)
        db.session.commit()
        return jsonify(message="Admin garantido/resetado com sucesso"), 200
    except SQLAlchemyError as e:
        current_app.logger.exception(f"Erro ao resetar admin: {e}")
        db.session.rollback()
        return jsonify(message="Erro ao resetar admin"), 500
