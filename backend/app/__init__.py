import os

from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS


def create_app() -> Flask:
    load_dotenv()

    frontend_dist = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../frontend/dist"
    )

    app = Flask(
        __name__,
        static_folder=frontend_dist,
        static_url_path=""
    )

    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

    CORS(app, supports_credentials=True)

    from .auth import auth_bp
    from .views import views_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)

    @app.route("/")
    def serve_index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        file_path = os.path.join(app.static_folder, path)

        if os.path.exists(file_path):
            return send_from_directory(app.static_folder, path)

        return send_from_directory(app.static_folder, "index.html")

    return app