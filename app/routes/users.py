
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Usuario
from ..utils import hash_password

users_bp = Blueprint('users_bp', __name__)


def require_admin():
    ident = get_jwt_identity()
    if not ident or ident.get('perfil') != 'admin':
        return False
    return True


@users_bp.get('')
@jwt_required()
def list_users():
    if not require_admin():
        return jsonify(message='Acesso negado'), 403
    users = Usuario.query.order_by(Usuario.criado_em.desc()).all()
    return jsonify(users=[{
        'id': u.id, 'nome': u.nome, 'email': u.email, 'perfil': u.perfil,
        'criado_em': u.criado_em.isoformat()
    } for u in users])


@users_bp.post('')
@jwt_required()
def create_user():
    if not require_admin():
        return jsonify(message='Acesso negado'), 403
    data = request.get_json() or {}
    nome = data.get('nome')
    email = (data.get('email') or '').strip().lower()
    senha = data.get('senha')
    perfil = data.get('perfil', 'tecnico')
    if not nome or not email or not senha:
        return jsonify(message='Campos obrigatórios: nome, email, senha'), 400
    if Usuario.query.filter_by(email=email).first():
        return jsonify(message='Email já cadastrado'), 409
    u = Usuario(nome=nome, email=email, senha_hash=hash_password(senha), perfil=perfil)
    db.session.add(u)
    db.session.commit()
    return jsonify(id=u.id, nome=u.nome, email=u.email, perfil=u.perfil), 201
