# app/services/rules_service.py

import json
import os
import re

class JsonRulesService:
    def __init__(self):
        self.db_path = "app\db\complete_rules_db.json"
        self.db = None
        self.is_loaded = False
    
    def load_db(self):
        """Load the rules database from JSON file"""
        if self.is_loaded:
            return {"status": "Database already loaded"}
        
        if not os.path.exists(self.db_path):
            print(f"Error: Rules database not found at {self.db_path}")
            return {"error": "Rules database not found"}
        
        try:
            print(f"Loading rules database from {self.db_path}")
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
            
            self.is_loaded = True
            print(f"Rules database loaded: {len(self.db.get('sections', {}))} sections, {len(self.db.get('rules', {}))} rules")
            return {"status": "Database loaded successfully"}
            
        except Exception as e:
            print(f"Error loading rules database: {str(e)}")
            return {"error": f"Failed to load rules database: {str(e)}"}
    
    def search_rules(self, query):
        """Search for rules matching the query"""
        if not self.is_loaded:
            self.load_db()
        
        if not self.db:
            return {"error": "Database not loaded"}
        
        results = []
        query = query.lower()
        
        # Case 1: Direct rule number search (e.g., "903.4")
        if re.match(r'^\d{3}(\.\d+[a-z]?)?$', query):
            # If it's just a section number (e.g., "903")
            if re.match(r'^\d{3}$', query) and query in self.db["sections"]:
                section = self.db["sections"][query]
                
                # Return the section and its rules
                section_rules = []
                for rule_id in section["rules"][:10]:  # Limit to first 10 rules
                    if rule_id in self.db["rules"]:
                        rule = self.db["rules"][rule_id]
                        section_rules.append({
                            "id": rule_id,
                            "text": rule["text"]
                        })
                
                results.append({
                    "type": "section",
                    "id": query,
                    "title": section["title"],
                    "rules": section_rules
                })
            
            # If it's a specific rule (e.g., "903.4")
            elif query in self.db["rules"]:
                rule = self.db["rules"][query]
                results.append({
                    "type": "rule",
                    "id": query,
                    "text": rule["text"],
                    "section_id": rule["section_id"],
                    "section_title": rule["section_title"],
                    "related_rules": rule.get("related_rules", [])
                })
            
            # If the exact rule isn't found, try partial matches
            else:
                for rule_id, rule in self.db["rules"].items():
                    if rule_id.startswith(query):
                        results.append({
                            "type": "rule",
                            "id": rule_id,
                            "text": rule["text"],
                            "section_id": rule["section_id"],
                            "section_title": rule["section_title"],
                            "related_rules": rule.get("related_rules", [])
                        })
                        
                        # Limit to 10 matching rules
                        if len(results) >= 10:
                            break
        
        # Case 2: Keyword search (e.g., "commander")
        else:
            # First check if the keyword is in the index
            if "keyword_index" in self.db and query in self.db["keyword_index"]:
                for rule_id in self.db["keyword_index"][query][:15]:  # Limit to first 15 results
                    if rule_id in self.db["rules"]:
                        rule = self.db["rules"][rule_id]
                        results.append({
                            "type": "rule",
                            "id": rule_id,
                            "text": rule["text"],
                            "section_id": rule["section_id"],
                            "section_title": rule["section_title"],
                            "related_rules": rule.get("related_rules", []),
                            "relevance": 3  # High relevance from keyword index
                        })
            
            # Also search in section titles for high relevance matches
            for section_id, section in self.db["sections"].items():
                if query in section["title"].lower():
                    # Get first 5 rules from this section
                    section_rules = []
                    for rule_id in section["rules"][:5]:
                        if rule_id in self.db["rules"]:
                            rule = self.db["rules"][rule_id]
                            section_rules.append({
                                "id": rule_id,
                                "text": rule["text"]
                            })
                    
                    results.append({
                        "type": "section",
                        "id": section_id,
                        "title": section["title"],
                        "rules": section_rules,
                        "relevance": 2  # Medium relevance for section matches
                    })
            
            # If we have too few results, do a full text search
            if len(results) < 5:
                # Only check a sample of rules for performance
                rule_items = list(self.db["rules"].items())[:5000]  # Limit search to 5000 rules
                for rule_id, rule in rule_items:
                    if query in rule["text"].lower():
                        # Check if this rule is already in results
                        if not any(r.get("id") == rule_id for r in results):
                            results.append({
                                "type": "rule",
                                "id": rule_id,
                                "text": rule["text"],
                                "section_id": rule["section_id"],
                                "section_title": rule["section_title"],
                                "related_rules": rule.get("related_rules", []),
                                "relevance": 1  # Lower relevance for text matches
                            })
                            
                            # Limit to 15 total results
                            if len(results) >= 15:
                                break
            
            # Sort by relevance (higher is better)
            results.sort(key=lambda x: -x.get("relevance", 0))
        
        return results[:15]  # Limit to top 15 results
    
    def get_section(self, section_id):
        """Get a complete section by ID"""
        if not self.is_loaded:
            self.load_db()
        
        if not self.db or section_id not in self.db["sections"]:
            return {"error": "Section not found"}
        
        section = self.db["sections"][section_id]
        section_rules = []
        
        for rule_id in section["rules"]:
            if rule_id in self.db["rules"]:
                rule = self.db["rules"][rule_id]
                section_rules.append({
                    "id": rule_id,
                    "text": rule["text"],
                    "related_rules": rule.get("related_rules", [])
                })
        
        return {
            "id": section_id,
            "title": section["title"],
            "rules": section_rules
        }
    
    def get_rule(self, rule_id):
        """Get a specific rule by ID"""
        if not self.is_loaded:
            self.load_db()
        
        if not self.db or rule_id not in self.db["rules"]:
            return {"error": "Rule not found"}
        
        rule = self.db["rules"][rule_id]
        return {
            "id": rule_id,
            "text": rule["text"],
            "section_id": rule["section_id"],
            "section_title": rule["section_title"],
            "related_rules": rule.get("related_rules", [])
        }
    
    def search_glossary(self, query):
        """Search the glossary for terms matching the query"""
        if not self.is_loaded:
            self.load_db()
        
        if not self.db or "glossary" not in self.db:
            return []
        
        results = []
        query = query.lower()
        
        # Search in glossary terms and definitions
        for term_key, term_data in self.db["glossary"].items():
            if query in term_key or query in term_data["definition"].lower():
                results.append(term_data)
        
        return results
    
    def get_commander_rules(self):
        """Get all rules related to the Commander format"""
        return self.get_section("903")