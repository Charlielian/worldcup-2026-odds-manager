import logging
import os
from flask import Flask
from backend.extensions import cors
from backend.config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging
    logging.basicConfig(
        level=logging.DEBUG if app.config['DEBUG'] else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Extensions
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])

    # Register blueprints
    from backend.routes.template_routes import templates_bp
    from backend.routes.api_routes import api_bp
    app.register_blueprint(templates_bp)
    app.register_blueprint(api_bp)

    return app
