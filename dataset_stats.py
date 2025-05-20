import re
import string
from collections import Counter

def extract_stats():
    """
    Extract statistics from domain.yml and nlu.yml files
    """
    # Load files
    with open('domain.yml', 'r', encoding='utf-8') as f:
        domain_content = f.read()
    
    try:
        with open('data/nlu.yml', 'r', encoding='utf-8') as f:
            nlu_content = f.read()
    except FileNotFoundError:
        # Try to open nlu.yml in the current directory
        with open('nlu.yml', 'r', encoding='utf-8') as f:
            nlu_content = f.read()
    
    # Extract statistics using regex
    
    # 1. Number of intents - find all lines that start with "- intent:" or are indented and start with "- "
    intent_lines = re.findall(r'^\s*- (?!.*-)\s*([^\n]+)', domain_content, re.MULTILINE)
    # Remove any non-intent lines (those that don't start with a letter)
    intent_lines = [line for line in intent_lines if line and not line.startswith('action_')]
    num_intents = len(intent_lines)
    
    # Alternative method: count all occurrences of "utter_" in domain.yml to identify intent responses
    utter_patterns = re.findall(r'utter_[a-zA-Z0-9_]+', domain_content)
    unique_utter_patterns = set(utter_patterns)
    num_intents_alt = len(unique_utter_patterns)
    
    # Also count intents in nlu.yml for verification
    nlu_intents = re.findall(r'- intent: ([^\n]+)', nlu_content)
    num_nlu_intents = len(nlu_intents)
    
    # Use the higher count as the result
    num_intents = max(num_intents, num_intents_alt, num_nlu_intents)
    
    # 2. Number of entities
    # Find all entities in domain.yml 
    entities_section = re.search(r'entities:(.*?)(?=^\w)', domain_content, re.DOTALL | re.MULTILINE)
    num_entities = 0
    if entities_section:
        entities_lines = re.findall(r'^\s*- ([^\n]+)', entities_section.group(1), re.MULTILINE)
        num_entities = len(entities_lines)
    
    # Also check for entity references in nlu.yml
    entity_refs = re.findall(r'\[([^]]+)\]\(([^)]+)\)', nlu_content)
    unique_entities = set(entity_type for _, entity_type in entity_refs)
    num_entities = max(num_entities, len(unique_entities))
    
    # 3. Number of responses - Using a simpler approach to count unique response templates
    # Find all response template names in the file
    response_templates = set()
    domain_lines = domain_content.split('\n')
    
    # First find the responses section
    start_line = 0
    for i, line in enumerate(domain_lines):
        if line.strip() == "responses:":
            start_line = i
            break
    
    # Collect all unique response templates
    for i in range(start_line, len(domain_lines)):
        line = domain_lines[i].strip()
        
        # Check if we've reached the end of the responses section
        if line.startswith('entities:') or line.startswith('slots:') or line.startswith('actions:'):
            break
        
        # Look for lines that define a response template (starts with utter_ and has a colon)
        if line.startswith('utter_') and ':' in line:
            template_name = line.split(':')[0].strip()
            response_templates.add(template_name)
    
    # Count the unique response templates
    response_count = len(response_templates)
    
    # 4. Process NLU data
    all_examples = []
    all_text = ""
    
    # Extract examples directly from the content
    # Looking for lines starting with "- " inside examples blocks
    nlu_lines = nlu_content.split('\n')
    in_examples_block = False
    
    for line in nlu_lines:
        line = line.strip()
        
        if "examples: |" in line:
            in_examples_block = True
            continue
            
        if in_examples_block:
            if line.startswith('- '):  # This is an example line
                example_text = line[2:].strip()  # Remove the "- " prefix
                if example_text:  # Ignore empty lines
                    all_examples.append(example_text)
                    all_text += " " + example_text
            elif line.startswith('- intent:') or not line:
                # New intent block or empty line means end of examples
                in_examples_block = False
    
    # Number of questions/examples
    num_questions = len(all_examples)
    
    # Clean text for tokenization
    all_text = all_text.lower()
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    all_text = all_text.translate(translator)
    
    # Split into tokens and count
    tokens = all_text.split()
    num_tokens = len(tokens)
    
    # Vocabulary size (unique tokens)
    vocabulary_size = len(set(tokens))
    
    # Calculate average tokens per question
    avg_tokens_per_question = round(num_tokens / num_questions, 2) if num_questions > 0 else 0
    
    # Calculate token frequency
    token_counter = Counter(tokens)
    most_common_tokens = token_counter.most_common(10)
    
    # Print debug info
    print(f"Debug - Intents from regex: {len(intent_lines)}")
    print(f"Debug - Intents from utter patterns: {len(unique_utter_patterns)}")
    print(f"Debug - Intents from nlu.yml: {num_nlu_intents}")
    print(f"Debug - Using highest count: {num_intents}")
    
    print(f"Debug - Entities from domain.yml: {num_entities}")
    if entity_refs:
        print(f"Debug - Unique entities found in nlu.yml: {unique_entities}")
    
    print(f"Debug - Response templates found: {response_count}")
    print(f"Debug - Response templates: {response_templates}")
    
    # Return statistics
    return {
        'Number of Intents': num_intents,
        'Number of Entities': num_entities,
        'Number of Responses': response_count,
        'Number of Questions': num_questions,
        'Number of Tokens': num_tokens,
        'Vocabulary Size': vocabulary_size,
        'Avg Tokens Per Question': avg_tokens_per_question
    }, most_common_tokens

def generate_latex_table(stats):
    """
    Generate a LaTeX table from the statistics
    """
    latex_table = """
\\begin{table}[h]
\\centering
\\begin{tabular}{|l|r|}
\\hline
\\textbf{Metric} & \\textbf{Count} \\\\
\\hline
"""
    
    for metric, count in stats.items():
        latex_table += f"{metric} & {count} \\\\\n"
    
    latex_table += """\\hline
\\end{tabular}
\\caption{Statistics of Congolese Swahili NLU Dataset}
\\label{tab:nlu_stats}
\\end{table}
"""
    return latex_table

def generate_common_tokens_table(common_tokens):
    """
    Generate a LaTeX table for most common tokens
    """
    latex_table = """
\\begin{table}[h]
\\centering
\\begin{tabular}{|l|r|}
\\hline
\\textbf{Token} & \\textbf{Frequency} \\\\
\\hline
"""
    
    for token, freq in common_tokens:
        latex_table += f"{token} & {freq} \\\\\n"
    
    latex_table += """\\hline
\\end{tabular}
\\caption{Most Common Tokens in Congolese Swahili NLU Dataset}
\\label{tab:common_tokens}
\\end{table}
"""
    return latex_table

if __name__ == "__main__":
    # Extract statistics
    stats, common_tokens = extract_stats()
    
    # Print statistics
    print("Dataset Statistics:")
    for metric, count in stats.items():
        print(f"{metric}: {count}")
    
    print("\nMost Common Tokens:")
    for token, freq in common_tokens:
        print(f"{token}: {freq}")
    
    # Generate and print LaTeX tables
    latex_table = generate_latex_table(stats)
    print("\nLaTeX Table for Statistics:")
    print(latex_table)
    
    tokens_table = generate_common_tokens_table(common_tokens)
    print("\nLaTeX Table for Common Tokens:")
    print(tokens_table) 