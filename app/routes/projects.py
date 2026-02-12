
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import Projeto, Log

projects_bp = Blueprint('projects_bp', __name__)


def current_user_id():
    ident = get_jwt_identity() or {}
    return ident.get('id')


def write_log(usuario_id, projeto_id, acao, antes=None, depois=None):
    log = Log(usuario_id=usuario_id, projeto_id=projeto_id, acao=acao, antes=antes, depois=depois)
    db.session.add(log)


@projects_bp.get('')
@jwt_required()
def list_projects():
    status = request.args.get('status')
    q = Projeto.query
    if status:
        q = q.filter_by(status=status)
    projetos = q.order_by(Projeto.criado_em.desc()).all()
    return jsonify(projects=[{
        'id': p.id,
        'nome': p.nome,
        'endereco': p.endereco,
        'status': p.status,
        'responsavel_id': p.responsavel_id,
        'custo_estimado': p.custo_estimado,
        'margem_prevista': p.margem_prevista,
        'viavel': p.viavel,
        'criado_em': p.criado_em.isoformat()
    } for p in projetos])


@projects_bp.post('')
@jwt_required()
def create_project():
    data = request.get_json() or {}
    nome = data.get('nome')
    if not nome:
        return jsonify(message='Campo nome é obrigatório'), 400
    p = Projeto(
        nome=nome,
        endereco=data.get('endereco'),
        status=data.get('status') or 'Em análise',
        responsavel_id=current_user_id(),
        custo_estimado=data.get('custo_estimado'),
        margem_prevista=data.get('margem_prevista'),
        viavel=data.get('viavel'),
    )
    db.session.add(p)
    db.session.commit()
    write_log(current_user_id(), p.id, 'criou_projeto', antes=None, depois={
        'nome': p.nome, 'status': p.status
    })
    db.session.commit()
    return jsonify(id=p.id), 201


@projects_bp.get('/<int:pid>')
@jwt_required()
def get_project(pid):
    p = Projeto.query.get_or_404(pid)
    return jsonify(id=p.id, nome=p.nome, endereco=p.endereco, status=p.status,
                   responsavel_id=p.responsavel_id, custo_estimado=p.custo_estimado,
                   margem_prevista=p.margem_prevista, viavel=p.viavel,
                   criado_em=p.criado_em.isoformat())


@projects_bp.put('/<int:pid>')
@jwt_required()
def update_project(pid):
    p = Projeto.query.get_or_404(pid)
    data = request.get_json() or {}
    before = {
        'nome': p.nome,
        'endereco': p.endereco,
        'status': p.status,
        'custo_estimado': p.custo_estimado,
        'margem_prevista': p.margem_prevista,
        'viavel': p.viavel,
    }
    p.nome = data.get('nome', p.nome)
    p.endereco = data.get('endereco', p.endereco)
    p.status = data.get('status', p.status)
    p.custo_estimado = data.get('custo_estimado', p.custo_estimado)
    p.margem_prevista = data.get('margem_prevista', p.margem_prevista)
    p.viavel = data.get('viavel', p.viavel)
    db.session.commit()
    after = {
        'nome': p.nome,
        'endereco': p.endereco,
        'status': p.status,
        'custo_estimado': p.custo_estimado,
        'margem_prevista': p.margem_prevista,
        'viavel': p.viavel,
    }
    write_log(current_user_id(), p.id, 'atualizou_projeto', antes=before, depois=after)
    db.session.commit()
    return jsonify(message='ok')


@projects_bp.delete('/<int:pid>')
@jwt_required()
def delete_project(pid):
    # Somente admin poderia deletar; checagem simples por perfil
    ident = get_jwt_identity()
    if ident.get('perfil') != 'admin':
        return jsonify(message='Apenas admin pode excluir'), 403
    p = Projeto.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    write_log(current_user_id(), pid, 'removeu_projeto')
    db.session.commit()
    return jsonify(message='ok')


@projects_bp.post('/<int:pid>/transition')
@jwt_required()
def transition(pid):
    p = Projeto.query.get_or_404(pid)
    data = request.get_json() or {}
    novo_status = data.get('status')
    observacao = data.get('observacao')
    if not novo_status:
        return jsonify(message='Informe o novo status'), 400
    before = {'status': p.status}
    p.status = novo_status
    db.session.commit()
    after = {'status': p.status}
    write_log(current_user_id(), p.id, f'transicao_status: {observacao or ""}'.strip(), antes=before, depois=after)
    db.session.commit()
    return jsonify(message='ok', status=p.status)
