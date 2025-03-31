from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.card_routes import card_bp
    app.register_blueprint(card_bp)

    from app.routes.rules_routes import rules_bp
    app.register_blueprint(rules_bp)

    return app
