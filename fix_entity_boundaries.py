#!/usr/bin/env python3
"""
Entity Boundary Fixer

This script fixes entity boundary issues in YAML NLU training data by:
1. Ensuring proper spacing between words
2. Fixing punctuation inside entity tags
3. Ensuring entity annotations match token boundaries
4. Fixing examples that don't start with a dash (-)
"""

import yaml
import re
import os
import argparse
from copy import deepcopy

def extract_entities(text):
    """Extract entity annotations from text and their positions"""
    # Match pattern [entity_text](entity_type)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    entities = []
    
    for match in re.finditer(pattern, text):
        entity_text = match.group(1)
        entity_type = match.group(2)
        start_idx = match.start()
        end_idx = match.end()
        
        entities.append({
            'text': entity_text,
            'type': entity_type,
            'start': start_idx,
            'end': end_idx,
            'original': match.group(0)  # The full [text](type) annotation
        })
    
    return entities

def fix_spacing(text):
    """Fix spacing issues around words and ensure punctuation is properly separated"""
    # Insert space before punctuation (keeping together common punctuation like ?!)
    text = re.sub(r'([a-zA-Z0-9])([,.;:!?])', r'\1 \2', text)
    
    # Fix spaces around parentheses
    text = re.sub(r'([a-zA-Z0-9])\(', r'\1 (', text)
    text = re.sub(r'\)([a-zA-Z0-9])', r') \1', text)
    
    # Remove double spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def fix_entity_boundaries(example):
    """Fix entity boundary issues in a single example"""
    # Skip if not a string (some examples might be integers or other types)
    if not isinstance(example, str):
        return example
    
    # Fix examples that don't start with a dash
    if not example.startswith('- ') and not example.startswith('-'):
        example = f"- {example.lstrip()}"
    
    # Remove leading dash for processing and restore it later
    has_dash = example.startswith('-')
    if has_dash:
        if example.startswith('- '):
            dash = '- '
            content = example[2:]
        else:
            dash = '-'
            content = example[1:]
    else:
        dash = ''
        content = example
    
    # Get entities before modifying the text
    entities = extract_entities(content)
    
    # Skip if no entities (nothing to fix)
    if not entities:
        return example
    
    # Remove entity annotations from the text to work with plain text
    plain_text = content
    offset = 0
    
    # Starting from the end to avoid index issues when replacing
    for entity in sorted(entities, key=lambda x: x['start'], reverse=True):
        start = entity['start']
        end = entity['end']
        entity_text = entity['text']
        
        # Remove the entity annotation
        plain_text = plain_text[:start] + entity_text + plain_text[end:]
    
    # Fix spacing in the plain text
    fixed_plain_text = fix_spacing(plain_text)
    
    # Now rebuild the annotated text with fixed entity boundaries
    # First, identify token boundaries in the fixed text
    tokens = []
    # Split by spaces but preserve entity text spans
    for token in fixed_plain_text.split():
        tokens.append(token)
    
    # Create a new structure for the text with proper entity annotations
    annotated_text = []
    processed_indices = set()
    
    for i, token in enumerate(tokens):
        # Skip tokens that were already processed as part of an entity
        if i in processed_indices:
            continue
        
        # Check if this token matches the start of any entity
        found_entity = False
        for entity in entities:
            entity_tokens = entity['text'].split()
            
            # Check if we have a match starting at this position
            if i + len(entity_tokens) <= len(tokens):
                # Check if all tokens match the entity
                if all(tokens[i+j].lower() == entity_tokens[j].lower().rstrip(',.;:!?') or 
                       tokens[i+j].lower().rstrip(',.;:!?') == entity_tokens[j].lower() 
                       for j in range(len(entity_tokens))):
                    # We found a match, add the full entity annotation
                    entity_text = ' '.join(tokens[i:i+len(entity_tokens)])
                    annotated_text.append(f"[{entity_text}]({entity['type']})")
                    
                    # Mark these tokens as processed
                    for j in range(i, i+len(entity_tokens)):
                        processed_indices.add(j)
                        
                    found_entity = True
                    break
        
        if not found_entity and i not in processed_indices:
            annotated_text.append(token)
    
    # Combine the tokens back into text
    fixed_example = ' '.join(annotated_text)
    
    # Restore the leading dash
    return f"{dash}{fixed_example}"

def process_yaml_file(input_file, output_file=None):
    """Process YAML file and fix entity boundary issues"""
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_fixed{ext}"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Create a copy to modify
    fixed_data = deepcopy(data)
    fixed_count = 0
    
    # Process each NLU block
    for i, nlu_item in enumerate(data.get('nlu', [])):
        if 'examples' in nlu_item:
            examples_text = nlu_item['examples']
            
            # Split examples into lines
            lines = examples_text.strip().split('\n')
            fixed_lines = []
            
            for line in lines:
                fixed_line = fix_entity_boundaries(line)
                if fixed_line != line:
                    fixed_count += 1
                fixed_lines.append(fixed_line)
            
            # Join the fixed lines back together
            fixed_examples = '\n'.join(fixed_lines)
            
            # Update the examples in the copy
            fixed_data['nlu'][i]['examples'] = fixed_examples
    
    # Write the fixed data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(fixed_data, f, allow_unicode=True, sort_keys=False)
    
    print(f"Entity boundary fixing complete. Fixed {fixed_count} examples.")
    print(f"Fixed data saved to: {output_file}")
    
    return fixed_count

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix entity boundary issues in NLU training data")
    parser.add_argument("input_file", help="Input YAML file path")
    parser.add_argument("--output_file", help="Output YAML file path", default=None)
    
    args = parser.parse_args()
    process_yaml_file(args.input_file, args.output_file) 