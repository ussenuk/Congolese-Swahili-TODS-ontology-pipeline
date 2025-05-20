import re

def update_domain_entities():
    # List of all unique entities found in nlu.yml
    all_entities = [
        'army_name', 'business_name', 'business_type', 'change_amount', 
        'country_name', 'currency_name', 'date', 'definition_word', 
        'device_name', 'device_type', 'doctor_type', 'drug_type', 
        'emotion_type', 'emotional_type', 'event_name', 'food_name', 
        'food_type', 'general_frequency', 'government_name', 'government_type', 
        'handicap_type', 'house_name', 'house_place', 'ingredient', 
        'ingredient_name', 'language_name', 'language_type', 'list_name', 
        'location', 'meal_type', 'measurement_type', 'medical_name', 
        'medical_type', 'medicine_name', 'medicine_type', 'mountain_name', 
        'order_type', 'organism_type', 'organization_name', 'organization_type', 
        'person', 'person_name', 'place_name', 'population_name', 'population_type', 
        'rebel_name', 'relation', 'request_type', 'salary_name', 'service_type', 
        'sickness_name', 'sickness_type', 'sikness_type', 'song_name', 
        'time', 'tribe_name', 'weather_descriptor'
    ]
    
    # Read domain.yml
    with open('domain.yml', 'r', encoding='utf-8') as f:
        domain_content = f.read()
    
    # Find the entities section
    entities_section_match = re.search(r'(entities:.*?)(?=^\w)', domain_content, re.DOTALL | re.MULTILINE)
    
    if entities_section_match:
        # Extract the existing entities section
        entities_section = entities_section_match.group(1)
        
        # Create new entities section
        new_entities_section = "entities:\n"
        for entity in sorted(all_entities):
            new_entities_section += f"  - {entity}\n"
        
        # Replace the old entities section with the new one
        updated_domain = domain_content.replace(entities_section, new_entities_section)
        
        # Write the updated domain.yml
        with open('domain.yml', 'w', encoding='utf-8') as f:
            f.write(updated_domain)
        
        print(f"Updated domain.yml with {len(all_entities)} entities")
    else:
        print("Could not find entities section in domain.yml")

if __name__ == "__main__":
    update_domain_entities() 