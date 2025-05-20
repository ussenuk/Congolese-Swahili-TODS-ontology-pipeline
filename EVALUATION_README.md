# Ontology Pipeline Evaluation Framework

This evaluation framework allows you to measure the effectiveness and efficiency of your ontology-based dialogue system. It implements the evaluation methodology described in the research paper, focusing on three key metrics:

1. **Task Completion Rate**: Measures how well the system completes tasks (success rate)
2. **Task Completion Cost**: Measures how efficiently the system completes tasks (turns needed)
3. **Edit Distance**: Measures how much the actual dialogue deviates from an ideal dialogue

## Quick Start

```bash
# Create sample dialogue data for testing
python annotate_dialogues.py --create-sample --sample-output raw_dialogues.txt

# Annotate dialogues with task information
python annotate_dialogues.py --input raw_dialogues.txt --output annotated_dialogues.json

# Run evaluation on annotated dialogues
python evaluate_ontology_pipeline.py --input annotated_dialogues.json --output evaluation_results.json

# Visualize the results
python visualize_results.py --input evaluation_results.json --output metrics_visualization.pdf
```

## Evaluation Process

The evaluation process consists of the following steps:

### 1. Collect Raw Dialogues

Record actual conversations between users and your ontology-based system. Save these in a text file with the following format:

```
User: What facilities are available in Camp A?
Bot: Camp A has 3 water points, 1 health facility, and 2 food distribution centers.
User: How many people can the health facility serve?
Bot: The health facility in Camp A can serve approximately 500 people per day.

User: Where can I find water in Sector B?
Bot: There are 2 water points in Sector B: one at the north entrance and one near the community center.
User: Is the water safe to drink?
Bot: Yes, all water points are treated and tested regularly for safety.
```

Note: Separate different dialogues with a blank line.

### 2. Annotate Dialogues

Run the annotation tool to mark each bot response with:
- Task types and success status
- Error types (if any)
- Ground truth responses (ideal responses)

```bash
python annotate_dialogues.py --input raw_dialogues.txt --output annotated_dialogues.json
```

The tool will guide you through the annotation process interactively.

### 3. Evaluate Performance

Run the evaluation script to calculate all metrics:

```bash
python evaluate_ontology_pipeline.py --input annotated_dialogues.json --output evaluation_results.json
```

### 4. Visualize Results

Generate visualizations of the evaluation metrics:

```bash
python visualize_results.py --input evaluation_results.json --output metrics_visualization.pdf
```

This creates a PDF with bar charts for each metric.

## Task Types

For ontology-based systems, we define the following task types:

1. **provide_information**: General information provision
2. **answer_query**: Direct answers to specific questions
3. **provide_entity_details**: Details about specific entities
4. **list_entities**: Enumerating entities matching criteria
5. **explain_relationship**: Explaining relationships between entities
6. **other**: Other task types not covered above

## Error Types

The framework tracks three types of errors:

1. **substitution**: Wrong information or answer
2. **deletion**: Missing information
3. **insertion**: Irrelevant or redundant information

## Creating Templates

You can create a template for dialogue annotation:

```bash
python evaluate_ontology_pipeline.py --create-template --template-output dialogue_template.json
```

## Requirements

- Python 3.7+
- matplotlib (for visualization)
- numpy

Install dependencies:

```bash
pip install matplotlib numpy
```

## Customization

You can customize the task types in both `evaluate_ontology_pipeline.py` and `annotate_dialogues.py` to better match your ontology domain. 