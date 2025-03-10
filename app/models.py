from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class Produto(db.Model):
    __tablename__ = 'produto'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Produto {self.nome}>'

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)  # Aumente para 255 caracteres

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)