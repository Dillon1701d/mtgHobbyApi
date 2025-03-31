from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from app.routes.card_routes import create_card_namespace
from app.routes.rules_routes import create_rules_namespace

def create_app():
    # Create Flask app
    app = Flask(__name__)
   
    # Enable CORS
    CORS(app)
   
    # Create a single API instance
    api = Api(app,
              version='1.0',
              title='MTG Hobby API',
              description='Comprehensive API for Magic: The Gathering Rules and Cards',
              doc='/docs')
   
    # Create namespaces using function that returns a namespace
    create_rules_namespace(api)
    create_card_namespace(api)
   
    return app

# For running the app directly
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)