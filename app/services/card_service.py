import json
import os

# Cache cards in memory after first load
_cached_cards = []

def load_all_cards():
    global _cached_cards
    if _cached_cards:
        return _cached_cards  # return cache if already loaded

    file_path = os.path.join("app", "db", "AllPrintings.json")
    with open(file_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    cards = []
    for set_data in all_data["data"].values():
        cards.extend(set_data.get("cards", []))

    _cached_cards = cards
    return cards

def search_cards_by_name(partial_name: str, page=1, per_page=20):
    partial_name = partial_name.lower()
    all_cards = load_all_cards()
    
    # Filter matching cards
    results = [
        card for card in all_cards
        if "name" in card and partial_name in card["name"].lower()
    ]
    
    # Calculate pagination details
    total_results = len(results)
    total_pages = (total_results + per_page - 1) // per_page
    
    # Slice results for current page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_results = results[start_index:end_index]
    
    return {
        'cards': paginated_results,
        'total_results': total_results,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }
