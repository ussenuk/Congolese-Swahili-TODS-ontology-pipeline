import yaml
import os
import random
import sys

# Function to load yaml file
def load_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = yaml.safe_load(f)
    return content

# Function to save yaml file
def save_yaml(content, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(content, f, allow_unicode=True, sort_keys=False)
    print(f"Saved to {file_path}")

# Check if the data file exists
data_file = 'data/nlu.yml'
if not os.path.exists(data_file):
    print(f"Error: {data_file} not found. Please make sure your data directory is properly set up.")
    sys.exit(1)

# Create tests directory if it doesn't exist
if not os.path.exists('tests'):
    os.makedirs('tests')

# Create data/train directory if it doesn't exist
train_dir = 'data/train'
if not os.path.exists(train_dir):
    os.makedirs(train_dir)

# Load the NLU data
nlu_data = load_yaml(data_file)

# Create a test set with 20% of the examples from each intent
test_data = {
    'version': nlu_data.get('version', '3.1'),
    'nlu': []
}

# Create a training set with the remaining 80% of examples
train_data = {
    'version': nlu_data.get('version', '3.1'),
    'nlu': []
}

# Process each intent in the NLU data
print("Splitting data into train and test sets...")
for intent_data in nlu_data.get('nlu', []):
    if 'intent' not in intent_data or 'examples' not in intent_data:
        continue
    
    intent = intent_data['intent']
    examples_str = intent_data['examples']
    
    # Extract examples (removing leading '- ')
    examples = [line.strip()[2:] for line in examples_str.split('\n') if line.strip().startswith('- ')]
    
    # Calculate how many examples to take for the test set (20%)
    num_test_examples = max(1, int(len(examples) * 0.2))
    
    # Make sure we don't try to sample more examples than are available
    num_test_examples = min(num_test_examples, len(examples))
    
    # Randomly select examples for the test set
    test_examples = random.sample(examples, num_test_examples)
    
    # The remaining examples go to the training set
    train_examples = [ex for ex in examples if ex not in test_examples]
    
    # Create a new intent entry for the test set with proper YAML formatting
    test_intent = {
        'intent': intent,
        'examples': '|\n' + '\n'.join([f'      - {example}' for example in test_examples])
    }
    
    # Create a new intent entry for the training set with proper YAML formatting
    train_intent = {
        'intent': intent,
        'examples': '|\n' + '\n'.join([f'      - {example}' for example in train_examples])
    }
    
    test_data['nlu'].append(test_intent)
    train_data['nlu'].append(train_intent)

# Save the test data with proper YAML formatting
with open('tests/test_data.yml', 'w', encoding='utf-8') as f:
    # Write version
    f.write(f"version: \"{test_data['version']}\"\n\n")
    
    # Write nlu section
    f.write("nlu:\n")
    
    # Write each intent with proper indentation
    for intent_data in test_data['nlu']:
        f.write(f"  - intent: {intent_data['intent']}\n")
        f.write(f"    examples: {intent_data['examples']}\n\n")

# Save the training data with proper YAML formatting
with open('data/train/train_data.yml', 'w', encoding='utf-8') as f:
    # Write version
    f.write(f"version: \"{train_data['version']}\"\n\n")
    
    # Write nlu section
    f.write("nlu:\n")
    
    # Write each intent with proper indentation
    for intent_data in train_data['nlu']:
        f.write(f"  - intent: {intent_data['intent']}\n")
        f.write(f"    examples: {intent_data['examples']}\n\n")

print(f"Created test set with examples from {len(test_data['nlu'])} intents")
print(f"Created training set with examples from {len(train_data['nlu'])} intents")
print("Test data saved to: tests/test_data.yml")
print("Training data saved to: data/train/train_data.yml") 