from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models import Usuario
from ..utils import hash_password

users_bp = Blueprint("users_bp", __name__)

@users_bp.get("")
@jwt_required()
def list_users():
    items = Usuario.query.order_by(Usuario.id.desc()).all()
    data = [{"id": u.id, "nome": u.nome, "email": u.email, "perfil": getattr(u, "perfil", "user")} for u in items]
    return jsonify(items=data), 200

@users_bp.post("")
@jwt_required()
def create_user():
    data = request.get_json() or {}
    nome = (data.get("nome") or "").strip()
    email = (data.get("email") or "").strip().lower()
    senha = data.get("senha") or ""
    perfil = data.get("perfil") or "user"
    if not nome or not email or not senha:
        return jsonify(message="nome, email e senha são obrigatórios"), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify(message="email já existe"), 409
    u = Usuario(nome=nome, email=email, senha_hash=hash_password(senha), perfil=perfil)
    db.session.add(u)
    db.session.commit()
    return jsonify(id=u.id), 201
