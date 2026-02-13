from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import Log

logs_bp = Blueprint("logs_bp", __name__)

@logs_bp.get("")
@jwt_required()
def list_logs():
    pid = request.args.get("project_id", type=int)
    q = Log.query
    if pid:
        q = q.filter_by(projeto_id=pid)
    items = q.order_by(Log.id.desc()).all()
    data = [{
        "id": l.id,
        "projeto_id": l.projeto_id,
        "acao": l.acao,
        "observacao": l.observacao,
        "criado_em": l.criado_em.isoformat()
    } for l in items]
    return jsonify(items=data), 200
