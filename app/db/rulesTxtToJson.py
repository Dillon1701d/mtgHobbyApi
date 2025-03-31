import re
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def extract_related_rules(rule_text):
    """Extract rule references from rule text"""
    related_rules = set()
    
    # Find references like "rule NNN" or "rule NNN.N"
    rule_refs = re.findall(r'rule\s+(\d{3}(?:\.\d+[a-z]?)?)', rule_text, re.IGNORECASE)
    related_rules.update(rule_refs)
    
    # Find references like "rules NNN.N and NNN.N"
    multi_refs = re.findall(r'rules\s+(\d{3}(?:\.\d+[a-z]?)?)(?:\s+and\s+|\s*,\s*)(\d{3}(?:\.\d+[a-z]?)?)', rule_text, re.IGNORECASE)
    for ref_pair in multi_refs:
        related_rules.update(ref_pair)
    
    # Find references to sections like "section N"
    section_refs = re.findall(r'section\s+(\d+)', rule_text, re.IGNORECASE)
    related_rules.update(section_refs)
    
    return list(related_rules)

def create_optimized_keyword_index(rules_db, max_word_frequency=300, min_word_length=3):
    """
    Create an optimized keyword index with lower memory footprint
    
    Args:
    - rules_db (dict): The rules database
    - max_word_frequency (int): Maximum allowed frequency for a word to be indexed
    - min_word_length (int): Minimum length of words to index
    
    Returns:
    dict: Optimized keyword index
    """
    # Common words to exclude
    common_words = {
        "the", "and", "for", "that", "with", "this", "from", "have", "their", 
        "when", "your", "you", "each", "may", "can", "any", "are", "its",
        "not", "one", "all", "card", "cards", "player", "players", "game",
        "spell", "spells", "ability", "abilities", "effect", "effects",
        "during", "until", "becomes", "become", "would", "instead", "rule",
        "see", "has", "other", "only", "some", "put", "time", "section"
    }
    
    # First pass - count words
    word_count = {}
    for rule_id, rule in rules_db["rules"].items():
        words = set(re.findall(rf'\b[a-zA-Z]{{{min_word_length},}}\b', rule["text"].lower()))
        for word in words:
            if word not in common_words:
                word_count[word] = word_count.get(word, 0) + 1
    
    # Build index, excluding overly common words
    keyword_index = {}
    for rule_id, rule in rules_db["rules"].items():
        words = set(re.findall(rf'\b[a-zA-Z]{{{min_word_length},}}\b', rule["text"].lower()))
        for word in words:
            # Only index words that aren't too common and aren't in common words list
            if word not in common_words and word_count.get(word, 0) <= max_word_frequency:
                keyword_index.setdefault(word, []).append(rule_id)
    
    return keyword_index

def process_rules_database(txt_file_path, json_output_path):
    """
    Convert MTG Rules text file to a structured JSON database
    
    Args:
    - txt_file_path (str): Path to the rules text file
    - json_output_path (str): Path to save the output JSON file
    
    Returns:
    dict: Processed rules database
    """
    # Read rules text file
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        rules_text = file.read()
    
    # Initialize data structure
    rules_db = {
        "metadata": {
            "title": "Magic: The Gathering Comprehensive Rules",
            "effective_date": None
        },
        "sections": {},
        "rules": {},
        "glossary": {}
    }
    
    # Extract effective date
    date_match = re.search(r"These rules are effective as of ([^\.]+)", rules_text)
    if date_match:
        rules_db["metadata"]["effective_date"] = date_match.group(1).strip()
    
    # Extract sections
    section_pattern = re.compile(r'^(\d{3})\.\s+(.+)$', re.MULTILINE)
    for match in section_pattern.finditer(rules_text):
        section_id = match.group(1)
        section_title = match.group(2).strip()
        
        rules_db["sections"][section_id] = {
            "id": section_id,
            "title": section_title,
            "rules": []
        }
    
    # Extract individual rules
    rule_pattern = re.compile(r'^(\d{3}\.(?:\d+[a-z]?))\.\s+(.+?)(?=\n\d{3}\.(?:\d+[a-z]?)\.|^\s*Glossary\s*$|\Z)', re.MULTILINE | re.DOTALL)
    for match in rule_pattern.finditer(rules_text):
        rule_id = match.group(1)
        rule_text = match.group(2).strip()
        
        # Clean up the rule text
        rule_text = re.sub(r'\n+', ' ', rule_text)
        rule_text = re.sub(r'\s+', ' ', rule_text)
        
        section_id = rule_id.split('.')[0]
        
        # Extract related rules
        related_rules = extract_related_rules(rule_text)
        
        # Store the rule
        rules_db["rules"][rule_id] = {
            "id": rule_id,
            "text": rule_text,
            "section_id": section_id,
            "section_title": rules_db["sections"].get(section_id, {}).get("title", "Unknown Section"),
            "related_rules": related_rules
        }
        
        # Add rule ID to the section's rules list
        if section_id in rules_db["sections"]:
            rules_db["sections"][section_id]["rules"].append(rule_id)
    
    # Create optimized keyword index
    rules_db["keyword_index"] = create_optimized_keyword_index(rules_db)
    
    # Save to JSON file
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(rules_db, f, indent=2)
    
    return rules_db

def process_glossary(glossary_file_path, rules_json_path=None, combined_json_path=None):
    """
    Process glossary file and optionally merge with rules database
    
    Args:
    - glossary_file_path (str): Path to glossary text file
    - rules_json_path (str, optional): Path to rules JSON file
    - combined_json_path (str, optional): Path to save combined JSON
    
    Returns:
    dict: Processed glossary database
    """
    # Read glossary text file
    with open(glossary_file_path, 'r', encoding='utf-8') as file:
        glossary_text = file.read()
    
    glossary_db = {}
    
    # Split the file by double newlines (which separate entries)
    entries = re.split(r'\n\s*\n', glossary_text)
    
    for entry in entries:
        if not entry.strip():
            continue
            
        # Split the first line (term) from the rest (definition)
        lines = entry.strip().split('\n')
        
        if not lines:
            continue
            
        term = lines[0].strip()
        
        # Skip entries like "See X" that are just references
        if term.startswith("See ") and len(lines) == 1:
            continue
            
        definition = ' '.join([line.strip() for line in lines[1:] if line.strip()])
        
        if term and definition:
            glossary_db[term.lower()] = {
                "term": term,
                "definition": definition,
                "related_rules": extract_related_rules(definition)
            }
        elif term and not definition and "See " in term:
            # Handle entries like "Forestcycling\nSee Typecycling."
            main_term = term.split("\n")[0].strip()
            ref_term = term.split("See ")[1].strip().rstrip(".")
            glossary_db[main_term.lower()] = {
                "term": main_term,
                "definition": f"See {ref_term}.",
                "reference_to": ref_term.lower()
            }
    
    # If rules_json_path is provided, merge the glossary with the rules
    if rules_json_path and combined_json_path:
        with open(rules_json_path, 'r', encoding='utf-8') as f:
            rules_db = json.load(f)
        
        # Add glossary to rules database
        rules_db["glossary"] = glossary_db
        
        # Save combined JSON
        with open(combined_json_path, 'w', encoding='utf-8') as f:
            json.dump(rules_db, f, indent=2)
        
        return rules_db
    
    return glossary_db

def main():
    """
    Main function to process MTG rules and glossary
    """
    # Define file paths
    rules_txt_file = "app/db/MagicCompRules 20250207.txt"
    glossary_txt_file = "app/db/MTG_Glossary.txt"
    rules_json = "app/db/rules_db.json"
    combined_json = "app/db/complete_rules_db.json"
    
    # Process the main rules file
    process_rules_database(rules_txt_file, rules_json)
    
    # Process the glossary if it exists
    if os.path.exists(glossary_txt_file):
        process_glossary(glossary_txt_file, rules_json, combined_json)
    else:
        # If no glossary, just copy the rules JSON to the combined JSON location
        with open(rules_json, 'r', encoding='utf-8') as f:
            rules_db = json.load(f)
        with open(combined_json, 'w', encoding='utf-8') as f:
            json.dump(rules_db, f, indent=2)

if __name__ == "__main__":
    main()