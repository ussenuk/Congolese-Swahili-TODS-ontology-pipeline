#!/usr/bin/env python3
"""
Intent Renaming Script

This script renames intents in a YAML file based on the most common words in their examples.
For each intent, it finds the three most frequently used significant words and combines them
to create a new intent name. It ensures uniqueness and preserves basic intents.
"""

import yaml
import re
import os
from collections import Counter
import argparse
from copy import deepcopy

# Words to exclude from analysis (common stopwords, punctuation, etc.)
STOPWORDS = set([
    "ni", "na", "kwa", "ya", "wa", "za", "la", "je", "ku", "iki", "aki", "ata", "nita", 
    "niki", "yaku", "ajili", "ana", "ako", "apa", "kama", "tuta", "wata", "weza", "kila", 
    "siku", "wapi", "pata", "toka", "kupata", "kuwa", "namna", "gani", "nini", "ina",
    "ili", "kila", "sasa", "hii", "hizi", "zake", "wangu", "wenye", "kwenye"
])

# Intents to preserve without renaming (basic dialog intents)
PRESERVE_INTENTS = [
    "greet_", "goodbye_", "affirm_", "deny_", "mood_great_", "mood_unhappy_", 
    "bot_challenge_", "who_are_you_", "thanks_", "help_", "stop_", "restart_",
    "query_health_facilities_", "query_water_sources_", "query_camps_", "submit_aid_request_"
]

def preprocess_text(text):
    """Clean and tokenize text for analysis"""
    # Remove entity annotations like [word](entity_type)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    # Tokenize
    tokens = text.split()
    # Remove stopwords and very short words
    tokens = [token for token in tokens if token not in STOPWORDS and len(token) > 2]
    return tokens

def find_common_words(examples_text):
    """Find the most common significant words in examples"""
    all_tokens = []
    
    # Split examples into individual lines
    examples = [line.strip() for line in examples_text.strip().split('\n')]
    
    # Process each example
    for example in examples:
        if example.startswith('-'):
            example = example[1:].strip()  # Remove the leading dash
            tokens = preprocess_text(example)
            all_tokens.extend(tokens)
    
    # Count word frequencies
    word_counts = Counter(all_tokens)
    
    # Get the three most common words (if there are at least three)
    most_common = word_counts.most_common(3)
    
    # If fewer than three words, use what we have
    top_words = [word for word, _ in most_common]
    
    return top_words

def should_preserve_intent(intent_name):
    """Check if the intent should be preserved (not renamed)"""
    for prefix in PRESERVE_INTENTS:
        if intent_name.startswith(prefix):
            return True
    return False

def generate_new_intent_name(top_words, original_name, used_names):
    """Generate new intent name from top words, ensuring uniqueness"""
    # If it's a preserved intent, don't rename it
    if should_preserve_intent(original_name):
        return original_name
    
    # If we couldn't find enough significant words, use parts of the original name
    if not top_words:
        return original_name
    
    # Create name from top words (up to 3)
    new_name = "_".join(top_words)
    
    # Keep the language suffix if present (e.g., _swa, _fr)
    lang_match = re.search(r'_(swa|fr|en)$', original_name)
    if lang_match:
        new_name += f"_{lang_match.group(1)}"
    
    # Check for uniqueness
    base_name = new_name
    counter = 1
    while new_name in used_names:
        # If name exists, add a counter
        if lang_match:
            # Extract without suffix
            name_without_suffix = base_name[:-4]  # Remove _swa, _fr, etc.
            new_name = f"{name_without_suffix}_{counter}{base_name[-4:]}"  # Add counter before suffix
        else:
            new_name = f"{base_name}_{counter}"
        counter += 1
    
    return new_name

def process_yaml_file(input_file, output_file):
    """Process the YAML file and rename intents"""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Create a copy to modify
    modified_data = deepcopy(data)
    
    # Create a mapping of old to new intent names
    intent_mapping = {}
    used_intent_names = set()
    
    # Process each NLU block
    for i, nlu_item in enumerate(data.get('nlu', [])):
        # Check if this is an intent definition
        if 'intent' in nlu_item and 'examples' in nlu_item:
            original_intent = nlu_item['intent']
            examples_text = nlu_item['examples']
            
            # Find common words
            top_words = find_common_words(examples_text)
            
            # Generate new unique intent name
            new_intent = generate_new_intent_name(top_words, original_intent, used_intent_names)
            
            # Record this name as used
            used_intent_names.add(new_intent)
            
            # Store the mapping
            intent_mapping[original_intent] = new_intent
            
            # Update the intent name in the copy
            modified_data['nlu'][i]['intent'] = new_intent
            
            if original_intent != new_intent:
                print(f"Renamed: {original_intent} -> {new_intent}")
            else:
                print(f"Preserved: {original_intent}")
    
    # Write the modified data back to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(modified_data, f, allow_unicode=True, sort_keys=False)
    
    print(f"\nIntent renaming complete. New file saved as: {output_file}")
    print(f"Total intents processed: {len(intent_mapping)}")
    print(f"Intents renamed: {sum(1 for old, new in intent_mapping.items() if old != new)}")
    print(f"Intents preserved: {sum(1 for old, new in intent_mapping.items() if old == new)}")
    
    # Create a mapping file for reference
    mapping_file = f"{os.path.splitext(output_file)[0]}_mapping.txt"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("Original Intent -> New Intent\n")
        f.write("-" * 40 + "\n")
        for old, new in intent_mapping.items():
            f.write(f"{old} -> {new}\n")
    
    print(f"Mapping file saved as: {mapping_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename intents based on common words in examples")
    parser.add_argument("input_file", help="Input YAML file path")
    parser.add_argument("--output_file", help="Output YAML file path", default=None)
    parser.add_argument("--preserve_all", action="store_true", help="Preserve all existing intents that start with query_, submit_, etc.")
    
    args = parser.parse_args()
    
    # If output file not specified, create a new filename
    if not args.output_file:
        base, ext = os.path.splitext(args.input_file)
        args.output_file = f"{base}_renamed{ext}"
    
    process_yaml_file(args.input_file, args.output_file) 