
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import Log

logs_bp = Blueprint('logs_bp', __name__)


@logs_bp.get('')
@jwt_required()
def list_logs():
    project_id = request.args.get('project_id', type=int)
    q = Log.query
    if project_id:
        q = q.filter_by(projeto_id=project_id)
    logs = q.order_by(Log.criado_em.desc()).limit(200).all()
    return jsonify(logs=[{
        'id': l.id,
        'usuario_id': l.usuario_id,
        'projeto_id': l.projeto_id,
        'acao': l.acao,
        'antes': l.antes,
        'depois': l.depois,
        'criado_em': l.criado_em.isoformat()
    } for l in logs])
