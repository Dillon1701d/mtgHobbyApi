import re
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def extract_related_rules(rule_text):
    """
    Extract rule references from rule text with improved pattern matching.
    
    This function finds rules that are explicitly referenced in the text of
    another rule, creating a network of related rules for easier navigation.
    
    Args:
    - rule_text (str): The text content of a rule to analyze
    
    Returns:
    list: Rule IDs referenced in the text
    """
    related_rules = set()
    
    # Pattern 1: Find references like "rule 123" or "rule 123.4" or "rule 123.4a"
    rule_refs = re.findall(r'rule\s+(\d{3}(?:\.\d+[a-z]?)?)', rule_text, re.IGNORECASE)
    related_rules.update(rule_refs)
    
    # Pattern 2: Find references like "rules 123.4 and 123.5"
    multi_refs = re.findall(r'rules\s+(\d{3}(?:\.\d+[a-z]?)?)(?:\s+and\s+|\s*,\s*)(\d{3}(?:\.\d+[a-z]?)?)', rule_text, re.IGNORECASE)
    for ref_pair in multi_refs:
        related_rules.update(ref_pair)
    
    # Pattern 3: Find references to sections like "section 123"
    section_refs = re.findall(r'section\s+(\d+)', rule_text, re.IGNORECASE)
    related_rules.update(section_refs)
    
    # Pattern 4: Direct rule number references like "see 123.4"
    direct_refs = re.findall(r'see\s+(?:rule\s+)?(\d{3}(?:\.\d+[a-z]?)?)', rule_text, re.IGNORECASE)
    related_rules.update(direct_refs)
    
    # Pattern 5: References in parentheses like "(see rule 123.4)"
    paren_refs = re.findall(r'\(\s*see\s+(?:rule\s+)?(\d{3}(?:\.\d+[a-z]?)?)\s*\)', rule_text, re.IGNORECASE)
    related_rules.update(paren_refs)
    
    # Pattern 6: Detect rules that appear at the beginning of sentences
    sentence_start_refs = re.findall(r'(\d{3}\.\d+[a-z]?)\.?\s+[A-Z]', rule_text)
    related_rules.update(sentence_start_refs)
    
    # Pattern 7: Detect cross-references to subrules like "701.3a–d"
    subrule_range_refs = re.findall(r'(\d{3}\.\d+[a-z]?)–[a-z]', rule_text)
    related_rules.update(subrule_range_refs)
    
    # Filter out invalid rule references and standardize format
    valid_related_rules = []
    for rule_ref in related_rules:
        # Clean up any trailing characters
        rule_ref = rule_ref.rstrip('.')
        rule_ref = rule_ref.rstrip(',')
        
        # Validate format
        if re.match(r'^\d{3}(?:\.\d+[a-z]?)?$', rule_ref):
            valid_related_rules.append(rule_ref)
    
    return sorted(valid_related_rules)

def create_optimized_keyword_index(rules_db, max_word_frequency=300, min_word_length=3):
    """
    Create an optimized keyword index with lower memory footprint
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

def extract_subrules(rule_id, rule_text):
    """
    Extract subrules from rule text that may contain embedded subrules.
    
    For example, from text like:
    "702.70. Poisonous 702.70a Poisonous is a triggered ability..."
    
    Args:
    - rule_id (str): ID of the main rule
    - rule_text (str): Text of the rule that may contain subrules
    
    Returns:
    tuple: (main_text, subrules_dict) where main_text is the text of the main rule only,
           and subrules_dict is a dictionary of extracted subrules
    """
    subrules_dict = {}
    
    # Base pattern for the rule ID without trailing period
    rule_base = rule_id.rstrip('.')
    
    # Pattern to match embedded subrules like "702.70a Poisonous is..."
    pattern = rf'{re.escape(rule_base)}([a-z])\s+(.+?)(?={re.escape(rule_base)}[a-z]|\Z)'
    
    # Find all embedded subrules
    subrule_matches = list(re.finditer(pattern, rule_text, re.DOTALL))
    
    if not subrule_matches:
        # No embedded subrules found
        return rule_text, {}
    
    # Extract the main rule text (everything before the first subrule)
    first_subrule_start = subrule_matches[0].start()
    main_text = rule_text[:first_subrule_start].strip()
    
    # Extract all subrules
    for match in subrule_matches:
        subrule_letter = match.group(1)
        subrule_text = match.group(2).strip()
        
        subrule_id = f"{rule_base}{subrule_letter}"
        
        # Extract related rules for this subrule using the enhanced function
        related_rules = extract_related_rules(subrule_text)
        
        subrules_dict[subrule_id] = {
            "id": subrule_id,
            "text": subrule_text,
            "section_id": rule_id.split('.')[0],
            "section_title": "",  # Will be filled in later
            "related_rules": related_rules,  # Using the enhanced related rules extraction
            "type": "rule",
            "is_subrule": True,
            "parent_rule_id": rule_base,
            "subrules": []  # Use empty list to store only subrule IDs, not full objects
        }
    
    return main_text, subrules_dict

def verify_rule_references(rules_db):
    """
    Verify and clean up rule references to ensure they point to valid rules.
    
    Args:
    - rules_db (dict): The rules database
    
    Returns:
    dict: The updated rules database with verified references
    """
    # Collect all valid rule IDs
    valid_rule_ids = set(rules_db["rules"].keys())
    valid_section_ids = set(rules_db["sections"].keys())
    
    # For each rule, verify its related_rules
    for rule_id, rule in rules_db["rules"].items():
        verified_related_rules = []
        
        for related_id in rule.get("related_rules", []):
            # Check if this is a section ID (3 digits)
            if re.match(r'^\d{3}$', related_id) and related_id in valid_section_ids:
                verified_related_rules.append(related_id)
                continue
                
            # Check if this is a valid rule ID
            if related_id in valid_rule_ids:
                verified_related_rules.append(related_id)
                continue
                
            # Check if this might be a partial rule ID (e.g., "704" instead of "704.1")
            # If it's a section ID, try to find the first rule in that section
            if re.match(r'^\d{3}$', related_id) and related_id in valid_section_ids:
                # Find the first rule in this section
                for potential_rule_id in valid_rule_ids:
                    if potential_rule_id.startswith(f"{related_id}.") and not rules_db["rules"][potential_rule_id].get("is_subrule", False):
                        verified_related_rules.append(potential_rule_id)
                        break
        
        # Update the rule with verified related_rules
        rule["related_rules"] = sorted(set(verified_related_rules))
    
    return rules_db

def process_rules_database(txt_file_path, json_output_path):
    """
    Convert MTG Rules text file to a structured JSON database with proper subrule handling
    and enhanced related rule extraction
    
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
    
    # Extract individual rules and their subrules
    # This pattern matches main rule headers like "702.70. Poisonous"
    rule_pattern = re.compile(r'^(\d{3}\.\d+)\.\s+(.+?)(?=^\d{3}\.\d+\.|\Z)', re.MULTILINE | re.DOTALL)
    
    for match in rule_pattern.finditer(rules_text):
        rule_id = match.group(1)
        full_rule_text = match.group(2).strip()
        
        # Extract section ID and get section title
        section_id = rule_id.split('.')[0]
        section_title = rules_db["sections"].get(section_id, {}).get("title", "Unknown Section")
        
        # Extract subrules from the full rule text
        main_rule_text, subrules = extract_subrules(rule_id, full_rule_text)
        
        # Clean up the main rule text
        main_rule_text = re.sub(r'\n+', ' ', main_rule_text)
        main_rule_text = re.sub(r'\s+', ' ', main_rule_text)
        
        # Extract related rules for the main rule using the enhanced function
        related_rules = extract_related_rules(main_rule_text)
        
        # Store the main rule
        rules_db["rules"][rule_id] = {
            "id": rule_id,
            "text": main_rule_text,
            "section_id": section_id,
            "section_title": section_title,
            "related_rules": related_rules,  # Using the enhanced related rules extraction
            "type": "rule",
            "is_subrule": False,
            "parent_rule_id": None,
            "subrules": list(subrules.keys())  # Store only the subrule IDs, not the full objects
        }
        
        # Add rule ID to the section's rules list
        if section_id in rules_db["sections"]:
            rules_db["sections"][section_id]["rules"].append(rule_id)
        
        # Add subrules to the main rules collection
        for subrule_id, subrule in subrules.items():
            # Set section title for all subrules
            subrule["section_title"] = section_title
            rules_db["rules"][subrule_id] = subrule
    
    # Verify and clean up rule references
    rules_db = verify_rule_references(rules_db)
    
    # Create optimized keyword index
    rules_db["keyword_index"] = create_optimized_keyword_index(rules_db)
    
    # Save to JSON file
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(rules_db, f, indent=2)
    
    # Count total and subrules
    total_rules = len(rules_db["rules"])
    subrules_count = sum(1 for rule in rules_db["rules"].values() if rule.get("is_subrule", False))
    parent_rules_count = total_rules - subrules_count
    
    logger.info(f"Total rules processed: {total_rules}")
    logger.info(f"Total parent rules: {parent_rules_count}")
    logger.info(f"Total subrules: {subrules_count}")
    
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
            # Extract related rules from the definition text
            related_rules = extract_related_rules(definition)
            
            glossary_db[term.lower()] = {
                "term": term,
                "definition": definition,
                "related_rules": related_rules  # Using the enhanced related rules extraction
            }
        elif term and not definition and "See " in term:
            # Handle entries like "Forestcycling\nSee Typecycling."
            main_term = term.split("\n")[0].strip()
            ref_term = term.split("See ")[1].strip().rstrip(".")
            glossary_db[main_term.lower()] = {
                "term": main_term,
                "definition": f"See {ref_term}.",
                "reference_to": ref_term.lower(),
                "related_rules": []  # Empty related rules for reference-only entries
            }
    
    # If rules_json_path is provided, merge the glossary with the rules
    if rules_json_path and combined_json_path:
        with open(rules_json_path, 'r', encoding='utf-8') as f:
            rules_db = json.load(f)
        
        # Add glossary to rules database
        rules_db["glossary"] = glossary_db
        
        # Verify glossary related rules against the rules database
        for term, term_data in glossary_db.items():
            if "related_rules" in term_data:
                verified_rules = []
                for rule_id in term_data["related_rules"]:
                    if rule_id in rules_db["rules"]:
                        verified_rules.append(rule_id)
                term_data["related_rules"] = verified_rules
        
        # Save combined JSON
        with open(combined_json_path, 'w', encoding='utf-8') as f:
            json.dump(rules_db, f, indent=2)
        
        return rules_db
    
    return glossary_db

def main():
    """
    Main function to process MTG rules and glossary with enhanced related rules
    """
    # Define file paths
    rules_txt_file = "app/db/MagicCompRules 20250207.txt"
    glossary_txt_file = "app/db/MTG_Glossary.txt"
    rules_json = "app/db/rules_db.json"
    combined_json = "app/db/complete_rules_db.json"
    
    logger.info("Processing rules text file...")
    # Process the main rules file
    rules_db = process_rules_database(rules_txt_file, rules_json)
    logger.info(f"Rules database created at {rules_json}")
    
    # Process the glossary if it exists
    if os.path.exists(glossary_txt_file):
        logger.info("Processing glossary file...")
        glossary_db = process_glossary(glossary_txt_file, rules_json, combined_json)
        logger.info(f"Combined rules and glossary database created at {combined_json}")
    else:
        logger.info("No glossary file found. Creating combined database with rules only.")
        # If no glossary, just copy the rules JSON to the combined JSON location
        with open(rules_json, 'r', encoding='utf-8') as f:
            rules_db = json.load(f)
        with open(combined_json, 'w', encoding='utf-8') as f:
            json.dump(rules_db, f, indent=2)
    
    # Print rule relationship statistics
    total_references = 0
    rules_with_references = 0
    for rule_id, rule in rules_db["rules"].items():
        if rule.get("related_rules") and len(rule["related_rules"]) > 0:
            rules_with_references += 1
            total_references += len(rule["related_rules"])
    
    logger.info("Processing complete.")
    logger.info("=== Rule Relationship Statistics ===")
    logger.info(f"Total rules processed: {len(rules_db['rules'])}")
    logger.info(f"Rules with references to other rules: {rules_with_references}")
    logger.info(f"Total rule references: {total_references}")
    if len(rules_db['rules']) > 0:
        logger.info(f"Average references per rule: {total_references / len(rules_db['rules']):.2f}")

if __name__ == "__main__":
    main()