from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    migrate = Migrate(app, db)  # Adicione esta linha

    with app.app_context():
        from . import routes
        db.create_all()
        routes.init_routes(app)

    return app