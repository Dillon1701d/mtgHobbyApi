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
            Search for cards by name
            
            Supports partial name matching
            Returns up to 50 results
            """
            name_query = request.args.get("name", "")
            
            if not name_query:
                cards_ns.abort(400, "Missing 'name' query parameter")
            
            cards = search_cards_by_name(name_query)
            return cards
    
    # Add the namespace to the API
    api.add_namespace(cards_ns, path='/cards')
    return cards_ns