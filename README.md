# Humanitarian Dialogue System with RDF Ontologies

A task-oriented dialogue system in Congolese Swahili for humanitarian assistance in displacement camps. This system integrates Rasa NLU with RDF ontologies to provide semantic query capabilities.

## Project Overview

This system helps displaced people and humanitarian workers access information about:
- Health facilities and services
- Water sources
- Food distribution
- Camp locations and facilities
- Security information

The system uses RDF (Resource Description Framework) to create a structured knowledge base that can be queried using SPARQL.

## Key Components

1. **RDF Ontology**: Defines humanitarian domain concepts using OWL/RDF
2. **Triple Store**: Stores RDF data and provides SPARQL query endpoint
3. **Rasa NLU**: Natural language understanding for Congolese Swahili
4. **Custom Actions**: Connect Rasa intents to SPARQL queries

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python requirements
pip install -r requirements.txt

# Additional packages for RDF support
pip install rdflib SPARQLWrapper
```

### 2. Set Up Triple Store

We recommend [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/) as the SPARQL server:

> **Important**: Apache Jena Fuseki 5.4.0 requires Java 17 or later. Please ensure you have the correct Java version installed before proceeding.

```bash
# Check your Java version
java -version

# Download and extract Fuseki
wget https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-5.4.0.zip
unzip apache-jena-fuseki-5.4.0.zip
cd apache-jena-fuseki-5.4.0

# Start Fuseki server (development mode)
./fuseki-server --mem /humanitarian
```

If you're using an older Java version and cannot upgrade, you can use an older version of Fuseki that is compatible with your Java installation:

```bash
# For Java 11, use Fuseki 4.x
wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.8.0.zip
unzip apache-jena-fuseki-4.8.0.zip
cd apache-jena-fuseki-4.8.0
./fuseki-server --mem /humanitarian
```

Or use the provided installation script:

```bash
bash scripts/install_and_setup_fuseki.sh
```

### 3. Load RDF Data

Convert the DTM DRC - BA North Kivu Excel data to RDF format:

```bash
# Convert Excel to RDF
python scripts/excel_to_rdf.py oim_rdc_dtm_mt_nord-kivu_2024_2_public_hdx.xlsx data/humanitarian_data.ttl

# Load initial ontology
curl -X POST --data-binary @ontology/humanitarian_ontology.ttl \
     --header "Content-Type:text/turtle" \
     http://localhost:3030/humanitarian/data

# Load converted data
curl -X POST --data-binary @data/humanitarian_data.ttl \
     --header "Content-Type:text/turtle" \
     http://localhost:3030/humanitarian/data
```

### 4. Configure Rasa Actions

Update the SPARQL endpoint in `actions/sparql_actions.py` if needed:

```python
SPARQL_ENDPOINT = "http://localhost:3030/humanitarian/query"
```

### 5. Train the Rasa Model

Before you can run the bot, you need to train the model:

```bash
# Train the Rasa model with the default config
rasa train

# Alternatively, use a specific config file
rasa train --config config_1.yml
```

### 6. Start Rasa Action Server

```bash
rasa run actions
```

### 7. Start Rasa Server

```bash
rasa run --enable-api --cors "*" #(optional)
```

### 8. Test with Rasa Shell

For interactive testing of the dialogue system:

```bash
# Basic shell for testing
rasa shell

# Debug mode with NLU details
rasa shell --debug

# Test with a specific model
rasa shell -m models/20240515-123456.tar.gz
```

## Usage Examples

### Example Queries in Congolese Swahili

1. **Health Facility Query**:
   - "Wapi hii ni vituo vya afya katika Goma?"
   - "Nataka kujua vituo vya afya vinavyotoa huduma ya chanjo"

2. **Water Source Query**:
   - "Chanzo cha maji katika Bulengo?"
   - "Vyanzo vya maji vilivyopo"

3. **Camp Information**:
   - "Kambi za wakimbizi wapi?"
   - "Kambi za wakimbizi katika Nyiragongo zina uwezo gani?"

4. **Aid Request**:
   - "Nahitaji msaada wa chakula"
   - "Ninaomba maji ya kunywa sasa"

## SPARQL Query Examples

Example SPARQL query to find health facilities offering vaccination services:

```sparql
PREFIX : <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?facility ?facilityName ?locName
WHERE {
    ?facility rdf:type :HealthFacility .
    ?facility rdfs:label ?facilityName .
    ?facility :hasLocation ?loc .
    ?loc rdfs:label ?locName .
    ?facility :providesService ?service .
    ?service rdfs:label ?serviceName .
    FILTER(REGEX(?serviceName, "Vaccination", "i"))
}
```

## Evaluation

For detailed information about how to evaluate the system, please refer to [EVALUATION_README.md](EVALUATION_README.md). This document describes the evaluation framework, metrics, and provides instructions for:

- Collecting and annotating dialogues
- Running the evaluation scripts
- Visualizing performance results
- Calculating task success metrics

The evaluation framework includes tools to measure task completion rate, dialogue efficiency, and response accuracy.

## Project Structure

```
.
├── actions/                      # Rasa custom actions
│   ├── actions.py                # Standard actions
│   ├── ontology_population.py    # Ontology data loading
│   ├── preprocessing.py          # Text preprocessing
│   ├── query_builder.py          # SPARQL query construction
│   └── sparql_actions.py         # SPARQL query execution
├── data/                         # Training data, RDF data
│   ├── humanitarian_data.ttl     # RDF data
│   ├── nlu_rdf.yml               # NLU training data for RDF
│   ├── rules_rdf.yml             # Rules for RDF responses
│   └── train/                    # Training data split
├── ontology/                     # RDF ontology definitions  
│   └── humanitarian_ontology.ttl # Main ontology file
├── scripts/                      # Utility scripts
│   ├── excel_to_rdf.py           # Excel to RDF converter
│   └── install_and_setup_fuseki.sh # Fuseki setup script
├── tests/                        # Test configuration
├── annotated_dialogues.json      # Evaluation dialogue data
├── config.yml                    # Rasa configuration
├── domain.yml                    # Domain definition
├── EVALUATION_README.md          # Evaluation documentation
├── raw_dialogues.txt             # User-bot conversation samples
├── requirements.txt              # Python dependencies
└── README.md                     # This documentation
```

## Contributing

Feel free to contribute to this project by:
1. Adding more domain concepts to the ontology
2. Improving the Congolese Swahili NLU data
3. Developing additional SPARQL queries
4. Enhancing the dialogue flow

## License

This project is open source under the MIT license. 