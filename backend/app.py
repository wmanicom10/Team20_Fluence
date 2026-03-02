from flask import Flask
from flask_cors import CORS

from config import Config
from routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    origins = [origin.strip() for origin in app.config.get("CORS_ORIGINS", "").split(",") if origin.strip()]
    CORS(app, resources={r"/api/*": {"origins": origins or "*"}})

    register_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
