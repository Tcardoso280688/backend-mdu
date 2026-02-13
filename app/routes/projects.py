from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Projeto, Log

projects_bp = Blueprint("projects_bp", __name__)

@projects_bp.get("")
@jwt_required()
def list_projects():
    items = Projeto.query.order_by(Projeto.id.desc()).all()
    data = []
    for p in items:
        data.append({
            "id": p.id,
            "nome": p.nome,
            "endereco": p.endereco,
            "status": p.status,
            "custo_estimado": float(p.custo_estimado) if p.custo_estimado is not None else None,
            "margem_prevista": float(p.margem_prevista) if p.margem_prevista is not None else None,
            "viavel": p.viavel
        })
    return jsonify(items=data), 200

@projects_bp.post("")
@jwt_required()
def create_project():
    data = request.get_json() or {}
    p = Projeto(
        nome=data.get("nome"),
        endereco=data.get("endereco"),
        status=data.get("status") or "Em análise",
        custo_estimado=data.get("custo_estimado"),
        margem_prevista=data.get("margem_prevista"),
        viavel=data.get("viavel")
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(id=p.id), 201

@projects_bp.post("/<int:pid>/transition")
@jwt_required()
def transition(pid: int):
    data = request.get_json() or {}
    novo_status = data.get("status")
    obs = data.get("observacao")
    if not novo_status:
        return jsonify(message="status é obrigatório"), 400
    p = Projeto.query.get_or_404(pid)
    p.status = novo_status
    db.session.add(p)
    # cria log da transição
    ident = get_jwt_identity() or {}
    log = Log(projeto_id=p.id, acao=f"transition:{novo_status}", observacao=obs, usuario_id=ident.get("id"))
    db.session.add(log)
    db.session.commit()
    return jsonify(message="ok"), 200
