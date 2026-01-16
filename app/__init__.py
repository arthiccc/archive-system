from flask import Flask
from app.config import config


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    from app.extensions import db, login_manager, csrf, migrate

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.auth.routes import auth
    from app.documents.routes import documents
    from app.search.routes import search
    from app.admin.routes import admin
    from app.api.routes import api
    from app.engines import engines

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(documents, url_prefix="/documents")
    app.register_blueprint(search, url_prefix="/search")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(engines, url_prefix="/engines")
    app.register_blueprint(api)

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 200

    @app.route("/")
    def index():
        from flask import redirect, url_for
        from flask_login import current_user

        if current_user.is_authenticated:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()

    return app
