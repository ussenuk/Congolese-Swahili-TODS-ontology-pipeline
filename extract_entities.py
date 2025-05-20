import re

# Function to extract entity types
def extract_entity_types():
    with open('data/nlu.yml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all patterns like [text](entity_type)
    pattern = r'\[.+?\]\(([a-z_]+)\)'
    matches = re.findall(pattern, content)
    
    # Get unique entity types
    unique_entities = sorted(set(matches))
    
    # Print results
    print(f"Found {len(unique_entities)} unique entity types in nlu.yml:")
    for entity in unique_entities:
        print(f"- {entity}")
    
    # Check which ones are missing from domain.yml
    with open('domain.yml', 'r', encoding='utf-8') as f:
        domain_content = f.read()
    
    # Extract the entities section from domain.yml
    entities_section = re.search(r'entities:\s*(?:-\s*([^\n]+))*', domain_content)
    domain_entities = []
    
    if entities_section:
        entities_text = entities_section.group(0)
        domain_entities = re.findall(r'-\s*([a-z_]+)', entities_text)
    
    missing_entities = [e for e in unique_entities if e not in domain_entities]
    
    print(f"\nEntities defined in domain.yml: {len(domain_entities)}")
    print(f"Entities missing from domain.yml: {len(missing_entities)}")
    
    if missing_entities:
        print("\nMissing entities that should be added to domain.yml:")
        for entity in missing_entities:
            print(f"  - {entity}")

if __name__ == "__main__":
    extract_entity_types() 