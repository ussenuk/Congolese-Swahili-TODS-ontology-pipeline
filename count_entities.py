import re

def count_entities():
    # Read domain.yml
    with open('domain.yml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the entities section
    entities_start = -1
    entities_end = -1
    
    for i, line in enumerate(lines):
        if line.strip() == 'entities:':
            entities_start = i + 1
        elif entities_start > 0 and line.strip() and not line.strip().startswith('-') and not line.startswith('  '):
            entities_end = i
            break
    
    if entities_start > 0 and entities_end > 0:
        # Extract entity lines
        entity_lines = lines[entities_start:entities_end]
        
        # Count entities
        entity_names = set()
        duplicates = []
        
        for line in entity_lines:
            line = line.strip()
            if line.startswith('- '):
                entity_name = line[2:].strip()
                if entity_name in entity_names:
                    duplicates.append(entity_name)
                else:
                    entity_names.add(entity_name)
        
        print(f"Total unique entities: {len(entity_names)}")
        print(f"Duplicated entities: {duplicates}")
        print(f"Total entries (including duplicates): {len(entity_names) + len(duplicates)}")
        
        # Print all entities
        print("\nAll entities:")
        for entity in sorted(entity_names):
            print(f"- {entity}")
    else:
        print("Could not find entities section in domain.yml")

if __name__ == "__main__":
    count_entities() 