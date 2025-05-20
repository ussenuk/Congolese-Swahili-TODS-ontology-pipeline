"""
Entity Recognition and Ontology Population

This module handles the recognition of entities in text
and population of the RDF ontology with those entities.
"""

import os
import sys
import logging
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD
import requests
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from actions.preprocessing import extract_and_preprocess_hdx_data, extract_humanitarian_concepts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Triple store configuration
FUSEKI_URL = "http://localhost:3030"
DATASET = "humanitarian"
QUERY_ENDPOINT = f"{FUSEKI_URL}/{DATASET}/query"
UPDATE_ENDPOINT = f"{FUSEKI_URL}/{DATASET}/update"

# Humanitarian ontology namespace
HUMANITARIAN = Namespace("http://example.org/humanitarian#")

def initialize_graph():
    """Initialize and return a new RDF graph with appropriate namespaces"""
    g = Graph()
    
    # Bind prefixes for easier reading
    g.bind("humanitarian", HUMANITARIAN)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    
    return g

def load_existing_ontology():
    """Load the existing humanitarian ontology from the triple store"""
    sparql = SPARQLWrapper(QUERY_ENDPOINT)
    
    # Query to get all triples
    query = """
    CONSTRUCT { ?s ?p ?o }
    WHERE { ?s ?p ?o }
    """
    
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        g = Graph()
        g.parse(data=results, format="json-ld")
        logger.info(f"Loaded {len(g)} triples from the triple store")
        return g
    except Exception as e:
        logger.error(f"Error loading ontology: {e}")
        return initialize_graph()

def recognize_entities(text, entity_model=None, rasa_entities=None):
    """
    Recognize humanitarian entities in text
    
    This function accepts entities from Rasa's DIET classifier and falls back to
    pattern matching only when Rasa entities are not provided.
    
    Args:
        text: Text to analyze
        entity_model: Optional entity recognition model
        rasa_entities: Entities detected by Rasa (list of dicts with 'entity' and 'value' keys)
        
    Returns:
        List of dictionaries with entity type and value
    """
    entities = []
    
    # If Rasa entities are provided, use them directly
    if rasa_entities and len(rasa_entities) > 0:
        logger.info(f"Using {len(rasa_entities)} entities detected by Rasa")
        
        for ent in rasa_entities:
            if 'entity' in ent and 'value' in ent:
                entity_type = ent['entity']
                entity_value = ent['value']
                
                # Map Rasa entity types to ontology entity types if needed
                type_mapping = {
                    'health_facility': 'health_facility',
                    'water_source': 'water_source',
                    'location': 'location',
                    'service_type': 'service',
                    'request_type': 'need',
                    'person': 'person',
                    'sickness_type': 'sickness',
                    'person_name': 'person'
                }
                
                mapped_type = type_mapping.get(entity_type, entity_type)
                
                entities.append({
                    "type": mapped_type,
                    "value": entity_value,
                    "start": ent.get('start', 0),
                    "end": ent.get('end', len(entity_value))
                })
        
        # If Rasa found entities, return them
        if entities:
            return entities
    
    # Fall back to pattern matching if no Rasa entities or mapping failed
    logger.info("Falling back to pattern matching for entity recognition")
    
    # Map patterns to entity types
    patterns = {
        "camp": ["camp", "site", "kambi", "settlement"],
        "health_facility": ["hospital", "clinic", "dispensary", "health center", "health centre", "afya", "hospitali", "kliniki"],
        "water_source": ["water", "source", "maji", "stream", "well", "borehole", "mayi", "majii", "robinet", "robinets", "kisima"],
        "location": ["goma", "nyiragongo", "rutshuru", "bulengo", "karisimbi", "masisi", "wapi", "fasi", "kambi"],
        "organization": ["unhcr", "unicef", "wfp", "who", "msf", "icrc", "ngo", "viongozi"],
        "service": ["education", "protection", "distribution", "vaccination", "treatment", "assistance", 
                   "tunziwa", "tunza", "tunzaka", "zalisha", "dawa", "ndui", "shoteya", "pokeya", "kamata"],
        "need": ["food", "shelter", "medicine", "security", "education", "chakula", "msaada", "mayi", "maji",
                "dawa", "usalama", "hema", "masomo", "kutunziwa", "blanketi", "sabuni", "nafasi", "pesa"],
        "person": ["watoto", "mtu", "wakimbizi", "watu", "batu", "bakimbizi", "familia", "mtoto"],
        "sickness_type": ["malaria", "malali", "ukimwi", "homa"]
    }
    
    text_lower = text.lower()
    
    for entity_type, keywords in patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Find the position of the keyword in the text
                pos = text_lower.find(keyword)
                
                # Extract the surrounding context
                start = max(0, text_lower.rfind(" ", 0, pos) + 1)
                end = text_lower.find(" ", pos + len(keyword))
                if end == -1:
                    end = len(text_lower)
                
                # Get the exact entity text from the original text
                entity_text = text[start:end]
                
                entities.append({
                    "type": entity_type,
                    "value": entity_text,
                    "start": start,
                    "end": end
                })
    
    return entities

def entity_to_rdf(entity, graph, ns=HUMANITARIAN):
    """
    Convert an entity to RDF triples and add to the graph
    
    Args:
        entity: Entity dictionary with type and value
        graph: RDF graph to add triples to
        ns: Namespace to use for URIs
        
    Returns:
        URI of the entity added to the graph
    """
    entity_type = entity["type"]
    entity_value = entity["value"]
    
    # Create a URI for the entity
    # Use slugified entity value for the URI
    slug = entity_value.lower().replace(" ", "_").replace("-", "_")
    uri = URIRef(f"{ns}{entity_type}_{slug}")
    
    # Add entity type triple
    if entity_type == "camp":
        graph.add((uri, RDF.type, ns.Camp))
    elif entity_type == "health_facility":
        graph.add((uri, RDF.type, ns.HealthFacility))
    elif entity_type == "water_source":
        graph.add((uri, RDF.type, ns.WaterSource))
    elif entity_type == "location":
        graph.add((uri, RDF.type, ns.Location))
    elif entity_type == "organization":
        graph.add((uri, RDF.type, ns.NGO))
    elif entity_type == "service":
        graph.add((uri, RDF.type, ns.HealthService))
    elif entity_type == "need":
        graph.add((uri, RDF.type, ns.Need))
    elif entity_type == "person":
        graph.add((uri, RDF.type, ns.DisplacedPerson))
    elif entity_type == "sickness_type":
        graph.add((uri, RDF.type, ns.HealthNeed))
    elif entity_type == "service_type":
        graph.add((uri, RDF.type, ns.HealthService))
    else:
        # Default to a generic entity
        graph.add((uri, RDF.type, ns.Entity))
    
    # Add label
    graph.add((uri, RDFS.label, Literal(entity_value)))
    
    # Add name property
    graph.add((uri, ns.name, Literal(entity_value)))
    
    return uri

def link_entities(entities, graph, ns=HUMANITARIAN):
    """
    Create relationships between entities based on their types
    
    Args:
        entities: List of entity dictionaries
        graph: RDF graph to add relationships to
        ns: Namespace to use for URIs
        
    Returns:
        Updated graph with entity relationships
    """
    # Group entities by type
    entity_by_type = {}
    for entity in entities:
        entity_type = entity["type"]
        if entity_type not in entity_by_type:
            entity_by_type[entity_type] = []
        entity_by_type[entity_type].append(entity)
    
    # Create relationship triples based on entity types
    # For example, link health facilities to locations
    if "health_facility" in entity_by_type and "location" in entity_by_type:
        for facility in entity_by_type["health_facility"]:
            facility_uri = entity_to_rdf(facility, graph, ns)
            
            for location in entity_by_type["location"]:
                location_uri = entity_to_rdf(location, graph, ns)
                graph.add((facility_uri, ns.hasLocation, location_uri))
    
    # Link camps to locations
    if "camp" in entity_by_type and "location" in entity_by_type:
        for camp in entity_by_type["camp"]:
            camp_uri = entity_to_rdf(camp, graph, ns)
            
            for location in entity_by_type["location"]:
                location_uri = entity_to_rdf(location, graph, ns)
                graph.add((camp_uri, ns.hasLocation, location_uri))
    
    # Link organizations to services they provide
    if "organization" in entity_by_type and "service" in entity_by_type:
        for org in entity_by_type["organization"]:
            org_uri = entity_to_rdf(org, graph, ns)
            
            for service in entity_by_type["service"]:
                service_uri = entity_to_rdf(service, graph, ns)
                graph.add((org_uri, ns.providesService, service_uri))
    
    # Link service_type entities to health facilities
    if "service_type" in entity_by_type and "health_facility" in entity_by_type:
        for service in entity_by_type["service_type"]:
            service_uri = entity_to_rdf(service, graph, ns)
            
            for facility in entity_by_type["health_facility"]:
                facility_uri = entity_to_rdf(facility, graph, ns)
                graph.add((facility_uri, ns.providesService, service_uri))
    
    # Link sickness_type to health facilities
    if "sickness_type" in entity_by_type and "health_facility" in entity_by_type:
        for sickness in entity_by_type["sickness_type"]:
            sickness_uri = entity_to_rdf(sickness, graph, ns)
            
            for facility in entity_by_type["health_facility"]:
                facility_uri = entity_to_rdf(facility, graph, ns)
                graph.add((facility_uri, ns.treats, sickness_uri))
    
    # Link persons to camps
    if "person" in entity_by_type and "camp" in entity_by_type:
        for person in entity_by_type["person"]:
            person_uri = entity_to_rdf(person, graph, ns)
            
            for camp in entity_by_type["camp"]:
                camp_uri = entity_to_rdf(camp, graph, ns)
                graph.add((person_uri, ns.registeredAt, camp_uri))
    
    # Link need entities to persons
    if "need" in entity_by_type and "person" in entity_by_type:
        for need in entity_by_type["need"]:
            need_uri = entity_to_rdf(need, graph, ns)
            
            for person in entity_by_type["person"]:
                person_uri = entity_to_rdf(person, graph, ns)
                graph.add((person_uri, ns.hasNeed, need_uri))
    
    return graph

def update_triple_store(graph):
    """
    Update the triple store with new triples from the graph
    
    Args:
        graph: RDF graph with triples to add
        
    Returns:
        True if update was successful, False otherwise
    """
    if len(graph) == 0:
        logger.warning("No triples to add to the triple store")
        return False
    
    # Serialize the graph to turtle format
    turtle_data = graph.serialize(format="turtle")
    
    # Use direct HTTP request instead of SPARQLWrapper
    url = f"{FUSEKI_URL}/{DATASET}/data"
    headers = {"Content-Type": "text/turtle"}
    
    try:
        response = requests.post(url, headers=headers, data=turtle_data)
        
        if response.status_code == 200 or response.status_code == 201:
            logger.info(f"Added {len(graph)} triples to the triple store")
            return True
        else:
            logger.error(f"Error updating triple store: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to triple store: {e}")
        return False

def process_hdx_data_for_ontology(excel_file_path, sheet_name=None):
    """
    Process HDX data from an Excel file, extract entities, and populate the ontology
    
    Args:
        excel_file_path: Path to the Excel file
        sheet_name: Name of the sheet to process
        
    Returns:
        True if processing was successful, False otherwise
    """
    # Extract and preprocess text from the Excel file
    sentences = extract_and_preprocess_hdx_data(excel_file_path, sheet_name)
    
    if not sentences:
        logger.warning("No sentences extracted from the Excel file")
        return False
    
    # Initialize a graph for the new triples
    graph = initialize_graph()
    
    # Process each sentence
    entity_count = 0
    for sentence in sentences:
        # Recognize entities in the sentence
        entities = recognize_entities(sentence)
        
        if entities:
            # Add entities to the graph
            for entity in entities:
                entity_to_rdf(entity, graph)
            
            # Link entities
            link_entities(entities, graph)
            
            entity_count += len(entities)
    
    logger.info(f"Recognized {entity_count} entities in {len(sentences)} sentences")
    
    # Update the triple store with the new triples
    success = update_triple_store(graph)
    
    return success

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ontology_population.py <excel_file_path> [sheet_name]")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = process_hdx_data_for_ontology(excel_file_path, sheet_name)
    
    if success:
        print("Successfully processed HDX data and updated the ontology")
    else:
        print("Failed to process HDX data or update the ontology") 