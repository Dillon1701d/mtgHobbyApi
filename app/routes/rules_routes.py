# app/routes/rules_routes.py
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services.rule_service import JsonRulesService

def create_rules_namespace(api):
    # Create a namespace for rules
    rules_ns = Namespace('rules', description='MTG Rules Operations')
    
    # Define models for documentation
    # Subrule model (for use in nested structures)
    subrule_model = rules_ns.model('Subrule', {
        'id': fields.String(description='Subrule identifier'),
        'text': fields.String(description='Subrule text')
    })
    
    # Main search result model with enhanced fields
    search_result_model = rules_ns.model('SearchResult', {
        'type': fields.String(description='Type of result (rule or section)'),
        'id': fields.String(description='Unique identifier'),
        'text': fields.String(description='Rule or section text'),
        'section_id': fields.String(description='Section identifier'),
        'section_title': fields.String(description='Section title'),
        'related_rules': fields.List(fields.String, description='Related rule numbers'),
        'is_subrule': fields.Boolean(description='Whether this is a subrule'),
        'parent_rule_id': fields.String(description='Parent rule ID (for subrules)'),
        'has_subrules': fields.Boolean(description='Whether this rule has subrules'),
        'subrule_count': fields.Integer(description='Number of subrules'),
        'subrules': fields.List(fields.Nested(subrule_model), description='List of subrules'),
        'relevance': fields.Integer(description='Search result relevance')
    })

    # Rule model for detailed rule views
    rule_detail_model = rules_ns.model('RuleDetail', {
        'id': fields.String(description='Rule identifier'),
        'text': fields.String(description='Rule text'),
        'section_id': fields.String(description='Section identifier'),
        'section_title': fields.String(description='Section title'),
        'related_rules': fields.List(fields.String, description='Related rule references'),
        'is_subrule': fields.Boolean(description='Whether this is a subrule'),
        'parent_rule': fields.Nested(rules_ns.model('ParentRule', {
            'id': fields.String(description='Parent rule identifier'),
            'text': fields.String(description='Parent rule text')
        }), description='Parent rule information'),
        'subrules': fields.List(fields.Nested(subrule_model), description='List of subrules'),
        'sibling_subrules': fields.List(fields.Nested(subrule_model), description='Other subrules of the same parent'),
        'referenced_rules': fields.List(fields.Nested(rules_ns.model('ReferencedRule', {
            'id': fields.String(description='Referenced rule identifier'),
            'text': fields.String(description='Referenced rule text'),
            'is_subrule': fields.Boolean(description='Whether this is a subrule')
        })), description='Rules referenced by this rule')
    })

    # Rule within section model
    section_rule_model = rules_ns.model('SectionRule', {
        'id': fields.String(description='Rule identifier'),
        'text': fields.String(description='Rule text'),
        'related_rules': fields.List(fields.String, description='Related rule references'),
        'has_subrules': fields.Boolean(description='Whether this rule has subrules'),
        'subrule_count': fields.Integer(description='Number of subrules'),
        'subrules': fields.List(fields.Nested(subrule_model), description='List of subrules')
    })

    # Section model
    section_model = rules_ns.model('Section', {
        'id': fields.String(description='Section identifier'),
        'title': fields.String(description='Section title'),
        'rules': fields.List(fields.Nested(section_rule_model), description='Rules in this section')
    })

    search_response_model = rules_ns.model('SearchResponse', {
        'results': fields.List(fields.Nested(search_result_model), 
                               description='List of search results')
    })

    glossary_result_model = rules_ns.model('GlossaryResult', {
        'term': fields.String(description='Glossary term'),
        'definition': fields.String(description='Term definition'),
        'related_rules': fields.List(fields.String, description='Related rule references'),
        'rule_references': fields.List(fields.Nested(rules_ns.model('GlossaryRuleReference', {
            'id': fields.String(description='Rule identifier'),
            'text': fields.String(description='Rule text')
        })), description='Rules referenced by this glossary term')
    })

    glossary_response_model = rules_ns.model('GlossaryResponse', {
        'results': fields.List(fields.Nested(glossary_result_model), 
                               description='List of glossary search results')
    })

    # Commander rules model including additional rules
    commander_rules_model = rules_ns.model('CommanderRules', {
        'id': fields.String(description='Section identifier'),
        'title': fields.String(description='Section title'),
        'rules': fields.List(fields.Nested(section_rule_model), description='Commander rules'),
        'additional_commander_rules': fields.List(fields.Nested(rules_ns.model('AdditionalRule', {
            'id': fields.String(description='Rule identifier'),
            'text': fields.String(description='Rule text'),
            'section_id': fields.String(description='Section identifier'),
            'section_title': fields.String(description='Section title')
        })), description='Additional rules related to Commander from other sections')
    })

    # Initialize rules service
    rules_service = JsonRulesService()

    # Search Rules Endpoint
    @rules_ns.route('/search')
    class RulesSearch(Resource):
        @rules_ns.doc(params={'q': 'Search query (rule number, keyword, etc.)'})
        @rules_ns.marshal_with(search_response_model)
        def get(self):
            """
            Search MTG rules
            
            Supports:
            - Rule numbers (e.g., 903.4, 702.70a)
            - Section numbers (e.g., 903)
            - Keywords (e.g., 'commander', 'casting')
            """
            query = request.args.get('q', '').strip()
            results = rules_service.search_rules(query)
            return {'results': results}

    # Get Section Endpoint
    @rules_ns.route('/section/<string:section_id>')
    class GetSection(Resource):
        @rules_ns.marshal_with(section_model)
        def get(self, section_id):
            """
            Get all rules for a specific section
            
            Returns the section title and all main rules in the section.
            Each rule includes information about any subrules it may have.
            """
            section_data = rules_service.get_section(section_id)
            
            if 'error' in section_data:
                rules_ns.abort(404, section_data['error'])
            
            return section_data

    # Get Rule Endpoint
    @rules_ns.route('/rule/<string:rule_id>')
    class GetRule(Resource):
        @rules_ns.marshal_with(rule_detail_model)
        def get(self, rule_id):
            """
            Get a specific rule by its full rule number
            
            Returns detailed information about the rule, including:
            - For main rules: Any subrules it contains
            - For subrules: The parent rule and sibling subrules
            - Referenced rules
            """
            rule_data = rules_service.get_rule(rule_id)
            
            if 'error' in rule_data:
                rules_ns.abort(404, rule_data['error'])
            
            return rule_data

    # Glossary Search Endpoint
    @rules_ns.route('/glossary/search')
    class GlossarySearch(Resource):
        @rules_ns.doc(params={'q': 'Glossary search term'})
        @rules_ns.marshal_with(glossary_response_model)
        def get(self):
            """
            Search the MTG glossary
            
            Returns glossary terms that match the search query,
            along with any rules they reference.
            """
            query = request.args.get('q', '').strip()
            results = rules_service.search_glossary(query)
            return {'results': results}

    # Commander Rules Endpoint
    @rules_ns.route('/commander')
    class CommanderRules(Resource):
        @rules_ns.marshal_with(commander_rules_model)
        def get(self):
            """
            Get all Commander format rules
            
            Returns all rules from section 903 (Commander) 
            plus additional rules from other sections that reference Commander.
            """
            commander_rules = rules_service.get_commander_rules()
            
            if 'error' in commander_rules:
                rules_ns.abort(404, commander_rules['error'])
            
            return commander_rules

    # Load the database when the namespace is created
    rules_service.load_db()

    # Add the namespace to the API
    api.add_namespace(rules_ns, path='/rules')

    return rules_ns