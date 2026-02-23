from flask import Flask
from config import Config
from routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
