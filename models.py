
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from .extensions import db

try:
    JSONType = JSON
except Exception:
    # Fallback para SQLite
    from sqlalchemy.types import JSON as JSONType

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(50), default='tecnico')  # tecnico|comercial|admin
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Projeto(db.Model):
    __tablename__ = 'projetos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    endereco = db.Column(db.String(255))
    status = db.Column(db.String(50), default='Em análise')
    responsavel_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    custo_estimado = db.Column(db.Float)
    margem_prevista = db.Column(db.Float)
    viavel = db.Column(db.Boolean, default=None)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    projeto_id = db.Column(db.Integer, db.ForeignKey('projetos.id'))
    acao = db.Column(db.String(255), nullable=False)
    antes = db.Column(JSONType)
    depois = db.Column(JSONType)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
