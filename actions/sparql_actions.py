"""
SPARQL Query Actions for Rasa

This module contains custom Rasa actions that can query an RDF triple store
using SPARQL to retrieve information based on user intents and entities.
It is customized for the humanitarian ontology for North Kivu.
"""

from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import logging

# Import our custom modules
from actions.preprocessing import extract_and_preprocess_hdx_data
from actions.ontology_population import recognize_entities, process_hdx_data_for_ontology
from actions.query_builder import process_nlu_for_query, get_query_for_intent, execute_query, format_query_results

logger = logging.getLogger(__name__)

# Configuration - update this according to your SPARQL endpoint setup
SPARQL_ENDPOINT = "http://localhost:3030/humanitarian/query"

def extract_rasa_entities(tracker):
    """Extract entities detected by Rasa from the tracker"""
    latest_message = tracker.latest_message
    if 'entities' in latest_message:
        return latest_message['entities']
    return []

class ActionQueryHealthFacilities(Action):
    """Query for health facilities based on location"""

    def name(self) -> Text:
        return "action_query_health_facilities"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract entities from the user message
        location = tracker.get_slot("location")
        
        # Extract all Rasa-detected entities
        rasa_entities = extract_rasa_entities(tracker)
        user_message = tracker.latest_message.get('text', '')
        
        # Log the detected entities
        logger.info(f"Rasa detected entities: {rasa_entities}")
        logger.info(f"User message: {user_message}")
        
        # Use the query builder to generate and execute the query
        slots = {"location": location} if location else {}
        
        # Process the NLU output and get a response
        response = process_nlu_for_query("query_health_facilities_swa", slots, rasa_entities)
        
        # Send the response to the user
        dispatcher.utter_message(text=response)
        
        return []


class ActionQueryWaterSources(Action):
    """Query for water sources based on location"""

    def name(self) -> Text:
        return "action_query_water_sources"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract entities from the user message
        location = tracker.get_slot("location")
        
        # Extract all Rasa-detected entities
        rasa_entities = extract_rasa_entities(tracker)
        user_message = tracker.latest_message.get('text', '')
        
        # Log the detected entities
        logger.info(f"Rasa detected entities: {rasa_entities}")
        logger.info(f"User message: {user_message}")
        
        # Use the query builder to generate and execute the query
        slots = {"location": location} if location else {}
        
        # Process the NLU output and get a response
        response = process_nlu_for_query("query_water_sources_swa", slots, rasa_entities)
        
        # Send the response to the user
        dispatcher.utter_message(text=response)
        
        return []


class ActionQueryCamps(Action):
    """Query for displacement camps based on location, capacity, manager, and coordinator"""

    def name(self) -> Text:
        return "action_query_camps"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract entities from the user message
        location = tracker.get_slot("location")
        
        # Extract all Rasa-detected entities
        rasa_entities = extract_rasa_entities(tracker)
        user_message = tracker.latest_message.get('text', '')
        
        # Log the detected entities
        logger.info(f"Rasa detected entities: {rasa_entities}")
        logger.info(f"User message: {user_message}")
        
        # Use the query builder to generate and execute the query
        slots = {"location": location} if location else {}
        
        # Process the NLU output and get a response
        response = process_nlu_for_query("query_camps_swa", slots, rasa_entities)
        
        # Send the response to the user
        dispatcher.utter_message(text=response)
        
        return []


class ActionSubmitAidRequest(Action):
    """Submit an aid request and find suitable organizations"""

    def name(self) -> Text:
        return "action_submit_aid_request"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract entities from the user message
        request_type = tracker.get_slot("request_type")
        location = tracker.get_slot("location")
        
        # Extract all Rasa-detected entities
        rasa_entities = extract_rasa_entities(tracker)
        user_message = tracker.latest_message.get('text', '')
        
        # Log the detected entities
        logger.info(f"Rasa detected entities: {rasa_entities}")
        logger.info(f"User message: {user_message}")
        
        # Use the query builder to generate and execute the query
        slots = {}
        if request_type:
            slots["request_type"] = request_type
        if location:
            slots["location"] = location
        
        # Process the NLU output and get a response
        response = process_nlu_for_query("submit_aid_request_swa", slots, rasa_entities)
        
        # Send the response to the user
        dispatcher.utter_message(text=response)
        
        return []


class ActionProcessHdxData(Action):
    """Process HDX data and populate the ontology"""

    def name(self) -> Text:
        return "action_process_hdx_data"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract the Excel file path from the user message or use the default
        excel_file = tracker.get_slot("file_path")
        if not excel_file:
            excel_file = "oim_rdc_dtm_mt_nord-kivu_2024_2_public_hdx.xlsx"
        
        # Process the HDX data and populate the ontology
        try:
            success = process_hdx_data_for_ontology(excel_file)
            
            if success:
                dispatcher.utter_message(text="Nimesindika data ya HDX na kuongeza ontolojia.")
            else:
                dispatcher.utter_message(text="Samahani, kulikuwa na shida wakati wa kusindika data ya HDX.")
        except Exception as e:
            logger.error(f"Error processing HDX data: {e}")
            dispatcher.utter_message(text="Samahani, kulikuwa na shida ya kiufundi. Tafadhali jaribu tena baadaye.")
        
        return []


class ActionCreateSparqlQuery(Action):
    """Create a SPARQL query from user input for debugging purposes"""

    def name(self) -> Text:
        return "action_create_sparql_query"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Extract the intent and entities from the user message
        intent = tracker.latest_message.get("intent", {}).get("name", "")
        
        # Extract all slots
        slots = {}
        for slot in tracker.slots:
            value = tracker.get_slot(slot)
            if value:
                slots[slot] = value
        
        # Extract Rasa-detected entities for debugging
        rasa_entities = extract_rasa_entities(tracker)
        user_message = tracker.latest_message.get('text', '')
        
        # Log the detected entities
        logger.info(f"Rasa detected entities: {rasa_entities}")
        logger.info(f"User message: {user_message}")
        
        # Generate the SPARQL query
        query = get_query_for_intent(intent, slots)
        
        if query:
            dispatcher.utter_message(text=f"Hoja ya SPARQL:\n```\n{query}\n```")
            
            # Also show detected entities for debugging
            if rasa_entities:
                entity_text = "\nEntities detected:\n"
                for entity in rasa_entities:
                    entity_text += f"- {entity.get('entity')}: {entity.get('value')}\n"
                dispatcher.utter_message(text=entity_text)
        else:
            dispatcher.utter_message(text="Samahani, sikuweza kuunda hoja ya SPARQL kwa ajili ya swali lako.")
        
        return []


class ActionRecognizeEntities(Action):
    """Recognize humanitarian entities in user input for debugging purposes"""

    def name(self) -> Text:
        return "action_recognize_entities"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get the user message
        user_message = tracker.latest_message.get("text", "")
        
        # Get entities from Rasa
        rasa_entities = extract_rasa_entities(tracker)
        
        # Use both Rasa entities and fallback pattern matching
        entities = recognize_entities(user_message, rasa_entities=rasa_entities)
        
        if entities:
            response = "Nimegundua vitu vifuatavyo:\n"
            for entity in entities:
                response += f"- {entity['value']} ({entity['type']})\n"
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text="Samahani, sikugundua vitu vyovyote katika ujumbe wako.")
        
        return [] 