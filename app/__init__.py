from flask import Flask
from .models import db
from .routes.main import main_bp
from .routes.menu import menu_bp
from .routes.cart import cart_bp
from .routes.payment import payment_bp
from flask_migrate import Migrate
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(main_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(payment_bp)

    return app