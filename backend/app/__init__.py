import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    CORS(app, supports_credentials=True, origins=[frontend_url])

    from .auth import auth_bp
    from .views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    return app
