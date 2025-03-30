from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.card_routes import card_bp
    app.register_blueprint(card_bp)

    return app
