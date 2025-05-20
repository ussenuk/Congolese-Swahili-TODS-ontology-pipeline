#!/usr/bin/env python3
"""
Combine multiple Rasa NLU files while preserving the correct YAML format
"""

import yaml
import sys
import os

def load_nlu_file(file_path):
    """Load NLU data from a YAML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data

def combine_nlu_files(output_file, *input_files):
    """Combine multiple NLU files and write to output file"""
    combined_nlu = []
    
    # Process each input file
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist. Skipping.")
            continue
            
        print(f"Loading {file_path}...")
        data = load_nlu_file(file_path)
        
        if 'nlu' not in data:
            print(f"Warning: No 'nlu' key found in {file_path}. Skipping.")
            continue
            
        # Add all intents to combined list
        for intent_data in data['nlu']:
            combined_nlu.append(intent_data)
    
    # Create combined structure
    combined_data = {
        'version': '3.1',
        'nlu': combined_nlu
    }
    
    # Custom YAML dumper to preserve the format Rasa expects
    class LiteralString(str):
        pass

    def literal_presenter(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

    # Register the presenter for multiline strings
    yaml.add_representer(LiteralString, literal_presenter)
    
    # Convert example strings to LiteralString to ensure correct formatting
    for intent in combined_data['nlu']:
        if 'examples' in intent and isinstance(intent['examples'], str):
            intent['examples'] = LiteralString(intent['examples'])
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(combined_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Successfully combined {len(input_files)} NLU files into {output_file}")
    print(f"Total intents: {len(combined_nlu)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python combine_nlu.py output.yml input1.yml input2.yml [input3.yml ...]")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    combine_nlu_files(output_file, *input_files) 