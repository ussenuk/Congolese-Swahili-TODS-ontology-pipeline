"""
SPARQL Query Builder

This module builds SPARQL queries from NLU intents and entities
detected by the DIET classifier.
"""

import logging
from typing import Dict, Any, List, Text, Optional
from SPARQLWrapper import SPARQLWrapper, JSON

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Triple store configuration
FUSEKI_URL = "http://localhost:3030"
DATASET = "humanitarian"
QUERY_ENDPOINT = f"{FUSEKI_URL}/{DATASET}/query"

class QueryTemplate:
    """
    A template for a SPARQL query associated with a specific intent
    """
    
    def __init__(self, name, query_template, required_entities=None, optional_entities=None):
        """
        Initialize a query template
        
        Args:
            name: Name of the query template
            query_template: SPARQL query template with placeholders for entities
            required_entities: List of required entity names
            optional_entities: List of optional entity names
        """
        self.name = name
        self.query_template = query_template
        self.required_entities = required_entities or []
        self.optional_entities = optional_entities or []
    
    def build_query(self, slots):
        """
        Build a SPARQL query from the template using slot values
        
        Args:
            slots: Dictionary of slot values from the NLU
            
        Returns:
            Complete SPARQL query with placeholders replaced by values,
            or None if required entities are missing
        """
        # Check if all required entities are present
        for entity in self.required_entities:
            if entity not in slots or not slots[entity]:
                logger.warning(f"Missing required entity '{entity}' for query template '{self.name}'")
                return None
        
        # Build query by replacing placeholders with values
        query = self.query_template
        
        # Replace placeholders for required entities
        for entity in self.required_entities:
            placeholder = f"{{{entity}}}"
            value = slots[entity]
            query = query.replace(placeholder, value)
        
        # Replace placeholders for optional entities if present
        for entity in self.optional_entities:
            placeholder = f"{{{entity}}}"
            if entity in slots and slots[entity]:
                value = slots[entity]
                query = query.replace(placeholder, value)
            else:
                # Handle optional entity absence by removing FILTER clauses
                # Find and remove FILTER clause containing the placeholder
                filter_start = query.find(f"FILTER(REGEX(?{entity}", 0)
                if filter_start != -1:
                    filter_end = query.find(")", filter_start) + 1
                    query = query[:filter_start] + query[filter_end:]
        
        return query

# Define query templates for common intents
QUERY_TEMPLATES = {
    "query_health_facilities_swa": QueryTemplate(
        name="health_facilities",
        query_template="""
PREFIX humanitarian: <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?facility ?facilityName ?loc ?locName
WHERE {
    ?facility rdf:type humanitarian:HealthFacility .
    ?facility rdfs:label ?facilityName .
    ?facility humanitarian:hasLocation ?loc .
    ?loc rdfs:label ?locName .
    FILTER(REGEX(?locName, "{location}", "i"))
}
        """,
        required_entities=[],
        optional_entities=["location"]
    ),
    
    "query_water_sources_swa": QueryTemplate(
        name="water_sources",
        query_template="""
PREFIX humanitarian: <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?source ?sourceName ?locName ?status
WHERE {
    ?source rdf:type humanitarian:WaterSource .
    ?source rdfs:label ?sourceName .
    ?source humanitarian:hasLocation ?loc .
    ?loc rdfs:label ?locName .
    ?source humanitarian:hasStatus ?status .
    FILTER(REGEX(?locName, "{location}", "i"))
}
        """,
        required_entities=[],
        optional_entities=["location"]
    ),
    
    "query_camps_swa": QueryTemplate(
        name="camps",
        query_template="""
PREFIX humanitarian: <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?camp ?campName ?locName ?capacity ?status
WHERE {
    ?camp rdf:type humanitarian:Camp .
    ?camp rdfs:label ?campName .
    ?camp humanitarian:hasLocation ?loc .
    ?loc rdfs:label ?locName .
    ?camp humanitarian:hasCapacity ?capacity .
    ?camp humanitarian:hasStatus ?status .
    FILTER(REGEX(?locName, "{location}", "i"))
}
        """,
        required_entities=[],
        optional_entities=["location"]
    ),
    
    "submit_aid_request_swa": QueryTemplate(
        name="aid_request",
        query_template="""
PREFIX humanitarian: <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?organization ?orgName ?locName ?service ?serviceName
WHERE {
    ?organization rdf:type humanitarian:NGO .
    ?organization rdfs:label ?orgName .
    ?organization humanitarian:providesService ?service .
    ?service rdfs:label ?serviceName .
    ?organization humanitarian:hasLocation ?loc .
    ?loc rdfs:label ?locName .
    FILTER(REGEX(?serviceName, "{request_type}", "i"))
    FILTER(REGEX(?locName, "{location}", "i"))
}
        """,
        required_entities=[],
        optional_entities=["request_type", "location"]
    )
}

def get_query_for_intent(intent, slots):
    """
    Get a SPARQL query for a specific intent using slot values
    
    Args:
        intent: Intent name from the NLU
        slots: Dictionary of slot values from the NLU
        
    Returns:
        Complete SPARQL query, or None if no matching template is found
    """
    if intent in QUERY_TEMPLATES:
        template = QUERY_TEMPLATES[intent]
        return template.build_query(slots)
    else:
        logger.warning(f"No query template found for intent '{intent}'")
        return None

def execute_query(query):
    """
    Execute a SPARQL query and return the results
    
    Args:
        query: SPARQL query to execute
        
    Returns:
        Query results as a dictionary, or None if execution fails
    """
    sparql = SPARQLWrapper(QUERY_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return None

def format_query_results(results, intent):
    """
    Format query results into a natural language response
    
    Args:
        results: Query results from execute_query
        intent: Intent name from the NLU
        
    Returns:
        Formatted response string in Congolese Swahili
    """
    if not results or 'results' not in results or not results['results']['bindings']:
        if intent == "query_health_facilities_swa":
            return "Samahani, hakuna vituo vya afya vilivyopatikana."
        elif intent == "query_water_sources_swa":
            return "Samahani, hakuna vyanzo vya maji vilivyopatikana."
        elif intent == "query_camps_swa":
            return "Samahani, hakuna kambi za wakimbizi zilizopatikana."
        elif intent == "submit_aid_request_swa":
            return "Samahani, hakuna mashirika yanayotoa huduma hiyo yaliyopatikana."
        else:
            return "Samahani, hakuna majibu yaliyopatikana."
    
    bindings = results['results']['bindings']
    
    # Format response based on intent
    if intent == "query_health_facilities_swa":
        response = "Hii ni vituo vya afya vilivyopo:\n"
        for binding in bindings:
            facility_name = binding.get('facilityName', {}).get('value', 'Unknown')
            location = binding.get('locName', {}).get('value', 'Unknown')
            response += f"- {facility_name} ({location})\n"
    
    elif intent == "query_water_sources_swa":
        response = "Hii ni vyanzo vya maji vilivyopo:\n"
        for binding in bindings:
            source_name = binding.get('sourceName', {}).get('value', 'Unknown')
            location = binding.get('locName', {}).get('value', 'Unknown')
            status = binding.get('status', {}).get('value', 'Unknown')
            response += f"- {source_name} ({location}) - {status}\n"
    
    elif intent == "query_camps_swa":
        response = "Hii ni kambi za wakimbizi ziliopo:\n"
        for binding in bindings:
            camp_name = binding.get('campName', {}).get('value', 'Unknown')
            location = binding.get('locName', {}).get('value', 'Unknown')
            capacity = binding.get('capacity', {}).get('value', 'Unknown')
            response += f"- {camp_name} ({location}) - Uwezo: {capacity}\n"
    
    elif intent == "submit_aid_request_swa":
        response = "Mashirika yanayotoa huduma hiyo:\n"
        for binding in bindings:
            org_name = binding.get('orgName', {}).get('value', 'Unknown')
            service_name = binding.get('serviceName', {}).get('value', 'Unknown')
            location = binding.get('locName', {}).get('value', 'Unknown')
            response += f"- {org_name} ({location}) - {service_name}\n"
    
    else:
        response = "Majibu yaliyopatikana:\n"
        # Generic response for other intents
        for i, binding in enumerate(bindings):
            response += f"Jibu {i+1}:\n"
            for var, value in binding.items():
                response += f"  {var}: {value['value']}\n"
    
    return response

def process_nlu_for_query(intent, slots, rasa_entities=None):
    """
    Process NLU output and execute a SPARQL query
    
    Args:
        intent: Intent name from the NLU
        slots: Dictionary of slot values from the NLU
        rasa_entities: Entities detected by Rasa (optional)
        
    Returns:
        Formatted response string in Congolese Swahili
    """
    # Build query from intent and slots
    query = get_query_for_intent(intent, slots)
    
    if not query:
        return "Samahani, sikuweza kuunda hoja kwa ajili ya swali lako."
    
    # Log the query for debugging
    logger.info(f"Executing SPARQL query: {query}")
    
    # Recognize entities and expand query if needed (using entities detected by Rasa)
    from actions.ontology_population import recognize_entities
    if rasa_entities:
        # For debugging, log the Rasa entities
        logger.info(f"Using {len(rasa_entities)} entities from Rasa for query enrichment")
    
    # Execute query
    results = execute_query(query)
    
    # Format results
    response = format_query_results(results, intent)
    
    return response 