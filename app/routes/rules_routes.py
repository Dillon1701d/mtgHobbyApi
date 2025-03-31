# app/routes/rules_routes.py
from flask import request
from flask_restx import Namespace, Resource, fields
from app.services.rule_service import JsonRulesService

def create_rules_namespace(api):
    # Create a namespace for rules
    rules_ns = Namespace('rules', description='MTG Rules Operations')
    
    # Define models for documentation
    search_result_model = rules_ns.model('SearchResult', {
        'type': fields.String(description='Type of result (rule or section)'),
        'id': fields.String(description='Unique identifier'),
        'text': fields.String(description='Rule or section text'),
        'section_id': fields.String(description='Section identifier'),
        'section_title': fields.String(description='Section title'),
        'related_rules': fields.List(fields.String, description='Related rule numbers'),
        'relevance': fields.Integer(description='Search result relevance')
    })

    search_response_model = rules_ns.model('SearchResponse', {
        'results': fields.List(fields.Nested(search_result_model), 
                               description='List of search results')
    })

    glossary_result_model = rules_ns.model('GlossaryResult', {
        'term': fields.String(description='Glossary term'),
        'definition': fields.String(description='Term definition')
    })

    glossary_response_model = rules_ns.model('GlossaryResponse', {
        'results': fields.List(fields.Nested(glossary_result_model), 
                               description='List of glossary search results')
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
            - Rule numbers (e.g., 903.4)
            - Section numbers (e.g., 903)
            - Keywords (e.g., 'commander', 'casting')
            """
            query = request.args.get('q', '').strip()
            results = rules_service.search_rules(query)
            return {'results': results}

    # Get Section Endpoint
    @rules_ns.route('/section/<string:section_id>')
    class GetSection(Resource):
        def get(self, section_id):
            """Get all rules for a specific section"""
            section_data = rules_service.get_section(section_id)
            
            if 'error' in section_data:
                rules_ns.abort(404, section_data['error'])
            
            return section_data

    # Get Rule Endpoint
    @rules_ns.route('/rule/<string:rule_id>')
    class GetRule(Resource):
        def get(self, rule_id):
            """Get a specific rule by its full rule number"""
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
            """Search the MTG glossary"""
            query = request.args.get('q', '').strip()
            results = rules_service.search_glossary(query)
            return {'results': results}

    # Commander Rules Endpoint
    @rules_ns.route('/commander')
    class CommanderRules(Resource):
        def get(self):
            """Get all Commander format rules"""
            commander_rules = rules_service.get_commander_rules()
            
            if 'error' in commander_rules:
                rules_ns.abort(404, commander_rules['error'])
            
            return commander_rules

    # Load the database when the namespace is created
    rules_service.load_db()

    # Add the namespace to the API
    api.add_namespace(rules_ns, path='/rules')

    return rules_ns