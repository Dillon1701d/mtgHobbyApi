# app/services/rules_service.py

import json
import os
import re

class JsonRulesService:
    def __init__(self):
        self.db_path = "app/db/complete_rules_db.json"
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
            
            # Count subrules for logging
            subrule_count = sum(1 for rule in self.db.get('rules', {}).values() 
                               if rule.get('is_subrule', False))
            
            print(f"Rules database loaded: {len(self.db.get('sections', {}))} sections, "
                  f"{len(self.db.get('rules', {}))} rules "
                  f"({subrule_count} subrules)")
            
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
        
        # Case 1: Direct rule number search (e.g., "903.4" or "702.70a")
        if re.match(r'^\d{3}(\.\d+[a-z]?)?$', query):
            # If it's just a section number (e.g., "903")
            if re.match(r'^\d{3}$', query) and query in self.db["sections"]:
                section = self.db["sections"][query]
                
                # Return the section and its main rules (not subrules)
                section_rules = []
                for rule_id in section["rules"][:10]:  # Limit to first 10 rules
                    if rule_id in self.db["rules"]:
                        rule = self.db["rules"][rule_id]
                        # Only include main rules, not subrules
                        if not rule.get("is_subrule", False):
                            section_rules.append({
                                "id": rule_id,
                                "text": rule["text"],
                                "has_subrules": len(rule.get("subrules", [])) > 0,
                                "subrule_count": len(rule.get("subrules", []))
                            })
                
                results.append({
                    "type": "section",
                    "id": query,
                    "title": section["title"],
                    "rules": section_rules
                })
            
            # If it's a specific rule (e.g., "903.4" or "702.70a")
            elif query in self.db["rules"]:
                rule = self.db["rules"][query]
                result = {
                    "type": "rule",
                    "id": query,
                    "text": rule["text"],
                    "section_id": rule["section_id"],
                    "section_title": rule["section_title"],
                    "related_rules": rule.get("related_rules", []),
                    "is_subrule": rule.get("is_subrule", False)
                }
                
                # If it's a subrule, include the parent rule ID
                if rule.get("is_subrule", False):
                    result["parent_rule_id"] = rule.get("parent_rule_id")
                # If it's a parent rule with subrules, include basic subrule info
                elif rule.get("subrules"):
                    subrules = []
                    for subrule_id in rule.get("subrules", []):
                        if subrule_id in self.db["rules"]:
                            subrule = self.db["rules"][subrule_id]
                            subrules.append({
                                "id": subrule_id,
                                "text": subrule["text"]
                            })
                    if subrules:
                        result["subrules"] = subrules
                
                results.append(result)
            
            # If the exact rule isn't found, try partial matches
            else:
                for rule_id, rule in self.db["rules"].items():
                    if rule_id.startswith(query):
                        # Only include main rules in partial matches, not subrules
                        if not rule.get("is_subrule", False) or query.endswith(rule_id[-1]):
                            results.append({
                                "type": "rule",
                                "id": rule_id,
                                "text": rule["text"],
                                "section_id": rule["section_id"],
                                "section_title": rule["section_title"],
                                "related_rules": rule.get("related_rules", []),
                                "is_subrule": rule.get("is_subrule", False),
                                "has_subrules": len(rule.get("subrules", [])) > 0,
                                "subrule_count": len(rule.get("subrules", []))
                            })
                        
                        # Limit to 15 matching rules
                        if len(results) >= 15:
                            break
        
        # Case 2: Keyword search (e.g., "commander")
        else:
            # First check if the keyword is in the index
            if "keyword_index" in self.db and query in self.db["keyword_index"]:
                for rule_id in self.db["keyword_index"][query][:15]:  # Limit to first 15 results
                    if rule_id in self.db["rules"]:
                        rule = self.db["rules"][rule_id]
                        result = {
                            "type": "rule",
                            "id": rule_id,
                            "text": rule["text"],
                            "section_id": rule["section_id"],
                            "section_title": rule["section_title"],
                            "related_rules": rule.get("related_rules", []),
                            "is_subrule": rule.get("is_subrule", False),
                            "has_subrules": len(rule.get("subrules", [])) > 0,
                            "subrule_count": len(rule.get("subrules", [])),
                            "relevance": 3  # High relevance from keyword index
                        }
                        
                        # If it's a subrule, include the parent rule ID
                        if rule.get("is_subrule", False):
                            result["parent_rule_id"] = rule.get("parent_rule_id")
                        
                        results.append(result)
            
            # Also search in section titles for high relevance matches
            for section_id, section in self.db["sections"].items():
                if query in section["title"].lower():
                    # Get first 5 main rules (non-subrules) from this section
                    section_rules = []
                    count = 0
                    for rule_id in section["rules"]:
                        if rule_id in self.db["rules"]:
                            rule = self.db["rules"][rule_id]
                            # Only include main rules, not subrules
                            if not rule.get("is_subrule", False):
                                section_rules.append({
                                    "id": rule_id,
                                    "text": rule["text"],
                                    "has_subrules": len(rule.get("subrules", [])) > 0,
                                    "subrule_count": len(rule.get("subrules", []))
                                })
                                count += 1
                                if count >= 5:
                                    break
                    
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
                # Focus on main rules first, as they're more likely what users want
                main_rules = {rule_id: rule for rule_id, rule in self.db["rules"].items() 
                             if not rule.get("is_subrule", False)}
                rule_items = list(main_rules.items())[:2000]  # Limit search to 2000 main rules
                
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
                                "is_subrule": False,
                                "has_subrules": len(rule.get("subrules", [])) > 0,
                                "subrule_count": len(rule.get("subrules", [])),
                                "relevance": 1  # Lower relevance for text matches
                            })
                            
                            # Limit to 15 total results
                            if len(results) >= 15:
                                break
                
                # If we still have too few results, search some subrules
                if len(results) < 5:
                    subrule_items = [(rule_id, rule) for rule_id, rule in self.db["rules"].items() 
                                    if rule.get("is_subrule", False)][:1000]  # Limit to 1000 subrules
                    
                    for rule_id, rule in subrule_items:
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
                                    "is_subrule": True,
                                    "parent_rule_id": rule.get("parent_rule_id"),
                                    "relevance": 0.5  # Lowest relevance for subrule text matches
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
                # Only include main rules (not subrules) in section view
                if not rule.get("is_subrule", False):
                    rule_info = {
                        "id": rule_id,
                        "text": rule["text"],
                        "related_rules": rule.get("related_rules", []),
                        "has_subrules": len(rule.get("subrules", [])) > 0,
                        "subrule_count": len(rule.get("subrules", []))
                    }
                    
                    # Optionally include basic subrule information
                    if rule.get("subrules"):
                        subrules = []
                        for subrule_id in rule.get("subrules", []):
                            if subrule_id in self.db["rules"]:
                                subrule = self.db["rules"][subrule_id]
                                subrules.append({
                                    "id": subrule_id,
                                    "text": subrule["text"]
                                })
                        rule_info["subrules"] = subrules
                    
                    section_rules.append(rule_info)
        
        return {
            "id": section_id,
            "title": section["title"],
            "rules": section_rules
        }
    
    def get_rule(self, rule_id):
        """Get a specific rule by ID with its context"""
        if not self.is_loaded:
            self.load_db()
        
        if not self.db or rule_id not in self.db["rules"]:
            return {"error": "Rule not found"}
        
        rule = self.db["rules"][rule_id]
        result = {
            "id": rule_id,
            "text": rule["text"],
            "section_id": rule["section_id"],
            "section_title": rule["section_title"],
            "related_rules": rule.get("related_rules", []),
            "is_subrule": rule.get("is_subrule", False)
        }
        
        # If it's a subrule, include the parent rule info
        if rule.get("is_subrule", False) and rule.get("parent_rule_id"):
            parent_id = rule.get("parent_rule_id")
            if parent_id in self.db["rules"]:
                parent_rule = self.db["rules"][parent_id]
                result["parent_rule"] = {
                    "id": parent_id,
                    "text": parent_rule["text"]
                }
                
                # Include sibling subrules
                sibling_subrules = []
                for sibling_id in parent_rule.get("subrules", []):
                    if sibling_id != rule_id and sibling_id in self.db["rules"]:
                        sibling = self.db["rules"][sibling_id]
                        sibling_subrules.append({
                            "id": sibling_id,
                            "text": sibling["text"]
                        })
                if sibling_subrules:
                    result["sibling_subrules"] = sibling_subrules
        
        # If it's a parent rule, include subrules
        elif rule.get("subrules"):
            subrules = []
            for subrule_id in rule.get("subrules", []):
                if subrule_id in self.db["rules"]:
                    subrule = self.db["rules"][subrule_id]
                    subrules.append({
                        "id": subrule_id,
                        "text": subrule["text"]
                    })
            if subrules:
                result["subrules"] = subrules
        
        # Include referenced rules if any
        if rule.get("related_rules"):
            referenced_rules = []
            for ref_id in rule.get("related_rules", []):
                if ref_id in self.db["rules"]:
                    ref_rule = self.db["rules"][ref_id]
                    referenced_rules.append({
                        "id": ref_id,
                        "text": ref_rule["text"],
                        "is_subrule": ref_rule.get("is_subrule", False)
                    })
            if referenced_rules:
                result["referenced_rules"] = referenced_rules
        
        return result
    
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
                # Include related rules if any
                term_result = dict(term_data)  # Create a copy of the term data
                
                # Enhance with rule references if they exist
                if "related_rules" in term_data and term_data["related_rules"]:
                    referenced_rules = []
                    for rule_id in term_data["related_rules"]:
                        if rule_id in self.db["rules"]:
                            rule = self.db["rules"][rule_id]
                            referenced_rules.append({
                                "id": rule_id,
                                "text": rule["text"]
                            })
                    if referenced_rules:
                        term_result["rule_references"] = referenced_rules
                
                results.append(term_result)
        
        return results
    
    def get_commander_rules(self):
        """Get all rules related to the Commander format"""
        section_data = self.get_section("903")
        
        # Also get any rules that reference "commander" from other sections
        if not self.is_loaded:
            self.load_db()
        
        additional_rules = []
        if "keyword_index" in self.db and "commander" in self.db["keyword_index"]:
            for rule_id in self.db["keyword_index"]["commander"]:
                # Skip rules that are already in section 903
                if rule_id.startswith("903"):
                    continue
                
                if rule_id in self.db["rules"]:
                    rule = self.db["rules"][rule_id]
                    # Only include main rules, not subrules
                    if not rule.get("is_subrule", False):
                        additional_rules.append({
                            "id": rule_id,
                            "text": rule["text"],
                            "section_id": rule["section_id"],
                            "section_title": rule["section_title"]
                        })
        
        if additional_rules:
            section_data["additional_commander_rules"] = additional_rules
            
        return section_data