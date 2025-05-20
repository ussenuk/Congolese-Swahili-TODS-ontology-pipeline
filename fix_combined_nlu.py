#!/usr/bin/env python3
"""
Directly combine Rasa NLU files while preserving the exact original format
"""

import sys
import os
import re

def combine_nlu_files(output_file, *input_files):
    """Combine NLU files by directly manipulating the raw text"""
    
    # Start with version header
    combined_content = "version: \"3.1\"\n\nnlu:\n"
    intent_count = 0
    
    # Process each input file
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist. Skipping.")
            continue
            
        print(f"Loading {file_path}...")
        
        # Read raw file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract the nlu section - find where it starts
        nlu_match = re.search(r'nlu:\s*\n', content)
        if not nlu_match:
            print(f"Warning: No 'nlu:' section found in {file_path}. Skipping.")
            continue
        
        # Get content after the nlu: line
        nlu_content = content[nlu_match.end():]
        
        # Find where the nlu section ends (next top-level key or end of file)
        next_section = re.search(r'\n\w+:\s*\n', nlu_content)
        if next_section:
            nlu_content = nlu_content[:next_section.start()]
        
        # Count intents in this file
        intent_matches = re.findall(r'- intent:', nlu_content)
        file_intent_count = len(intent_matches)
        intent_count += file_intent_count
        
        # Add the content to our combined file
        combined_content += nlu_content
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(combined_content)
    
    print(f"Successfully combined {len(input_files)} NLU files into {output_file}")
    print(f"Total intents: {intent_count}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python fix_combined_nlu.py output.yml input1.yml input2.yml [input3.yml ...]")
        sys.exit(1)
    
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    
    combine_nlu_files(output_file, *input_files) 