# app/routes/card_routes.py
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services.card_service import search_cards_by_name

def create_card_namespace(api):
    # Create a namespace for cards
    cards_ns = Namespace('cards', description='MTG Card Search Operations')
    
    # Define card model for documentation
    card_model = cards_ns.model('Card', {
        'name': fields.String(description='Card name'),
        'manaCost': fields.String(description='Mana cost of the card', required=False),
        'type': fields.String(description='Card type'),
        'rarity': fields.String(description='Card rarity'),
        'setCode': fields.String(description='Set code the card belongs to'),
        'text': fields.String(description='Card text/ability', required=False),
        'uuid': fields.String(description='Unique identifier for the card'),
        # Add more fields as needed based on the Sol Ring example
        'artist': fields.String(description='Card artist name', required=False),
        'colors': fields.List(fields.String, description='Card colors', required=False),
        'legalities': fields.Raw(description='Card legalities in different formats', required=False)
    })

    card_search_response_model = cards_ns.model('CardSearchResponse', {
        'cards': fields.List(fields.Nested(card_model), description='List of matching cards')
    })

    # Card Search Endpoint
    @cards_ns.route('/')
    class CardSearch(Resource):
        @cards_ns.doc(params={'name': 'Partial card name to search'})
        @cards_ns.expect(cards_ns.parser().add_argument('name', location='args', required=True))
        @cards_ns.marshal_with(card_search_response_model)
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
            return {'cards': cards}

    # Add the namespace to the API
    api.add_namespace(cards_ns, path='/cards')

    return cards_ns