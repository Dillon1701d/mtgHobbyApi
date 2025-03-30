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

def search_cards_by_name(partial_name: str):
    partial_name = partial_name.lower()
    all_cards = load_all_cards()
    results = [
        card for card in all_cards
        if "name" in card and partial_name in card["name"].lower()
    ]
    return results[:50]  # limit to top 50 results
