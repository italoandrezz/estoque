import os

class Config:
    SECRET_KEY = '7OW6WTOAOZM6X'  # Chave secreta para segurança do Flask
    SQLALCHEMY_DATABASE_URI = 'postgresql://estoque_user:327295@localhost/estoque'
    SQLALCHEMY_TRACK_MODIFICATIONS = False