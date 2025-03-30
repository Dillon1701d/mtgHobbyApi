from flask import Blueprint, jsonify, request
from app.services.card_service import search_cards_by_name

card_bp = Blueprint("cards", __name__, url_prefix="/api/cards")

@card_bp.route("/", methods=["GET"])
def fetch_cards():
    name_query = request.args.get("name", "")
    if not name_query:
        return jsonify({"error": "Missing 'name' query parameter"}), 400

    cards = search_cards_by_name(name_query)
    return jsonify(cards)
