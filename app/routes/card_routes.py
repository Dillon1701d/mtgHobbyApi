# app/routes/card_routes.py
from flask import request
from flask_restx import Namespace, Resource
from app.services.card_service import search_cards_by_name

def create_card_namespace(api):
    # Create a namespace for cards
    cards_ns = Namespace('cards', description='MTG Card Search Operations')
    
    # Card Search Endpoint
    @cards_ns.route('/')
    class CardSearch(Resource):
        def get(self):
            """
            Search for cards by name with pagination
            """
            name_query = request.args.get("name", "")
            page = int(request.args.get("page", 1))
            per_page = int(request.args.get("per_page", 20))
            
            if not name_query:
                cards_ns.abort(400, "Missing 'name' query parameter")
            
            return search_cards_by_name(name_query, page, per_page)
        
    # Add the namespace to the API
    api.add_namespace(cards_ns, path='/cards')
    return cards_ns