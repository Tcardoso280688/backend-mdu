from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Usuario
from ..utils import verify_password

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.post('/login')
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    senha = data.get('senha') or ''
    if not email or not senha:
        return jsonify(message='Email e senha são obrigatórios'), 400

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        return jsonify(message='Credenciais inválidas'), 401

    # >>> USE o MESMO CAMPO do seu models (senha_hash OU password_hash)
    if not verify_password(getattr(user, 'senha_hash', None) or getattr(user, 'password_hash', ''), senha):
        return jsonify(message='Credenciais inválidas'), 401

    token = create_access_token(identity={
        'id': user.id, 'email': user.email, 'perfil': user.perfil, 'nome': user.nome
    })
    return jsonify(access_token=token, user={
        'id': user.id, 'email': user.email, 'perfil': user.perfil, 'nome': user.nome
    })
