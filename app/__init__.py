from flask import Flask
import os
from .models import db, User
from .extensions import bcrypt, limiter
from .routes.main import main_bp
from .routes.menu import menu_bp
from .routes.cart import cart_bp
from .routes.payment import payment_bp
from .routes.auth import auth_bp
from .routes.admin import admin_bp
from .routes.analytics import analytics_bp
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # If a reverse proxy (nginx, a cloud load balancer, ...) forwards the
    # app, trust X-Forwarded-For so the rate limiter keys on the real
    # client IP instead of the proxy address. Inert in local dev.
    if os.environ.get('TRUST_PROXY', '').lower() in ('1', 'true', 'yes'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    Migrate(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import request, jsonify, redirect, url_for
        if request.path.startswith('/api/'):
            return jsonify({"error": "Unauthorized", "redirect": "/login"}), 401
        return redirect(url_for('auth.login'))

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        from flask import request, jsonify, render_template
        if request.path.startswith('/api/'):
            return jsonify({"error": "Too many requests. Please try again shortly."}), 429
        return render_template('rate_limited.html'), 429

    app.register_blueprint(main_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)

    return app