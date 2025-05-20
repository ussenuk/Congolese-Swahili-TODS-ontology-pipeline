import streamlit as st
import subprocess
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from rasa.model_training import train
from rasa.shared.nlu.training_data.loading import load_data
from rasa.shared.nlu.training_data.message import Message
from rasa.shared.utils.io import read_config_file
from rasa.model import get_latest_model
from rasa.nlu.test import run_evaluation
import tempfile

st.set_page_config(page_title="Rasa Model Comparison", layout="wide")
st.title("Rasa Model Comparison for Humanitarian ToDS")

# Define configurations
configs = {
    "Config_1": "config_1.yml",  # Sparse features + LaBSE
    "Config_1_b": "config_1_b.yml",  # Sparse features + AfroXLMR
    "Config_2": "config_2.yml",  # Dense features only (XLM-RoBERTa)
    "Config_2_b": "config_2_b.yml",  # Dense features only (AfriMT5)
    "Config_3": "config_3.yml",  # Sparse features only (lightweight)
}

# Sidebar for model selection and actions
st.sidebar.header("Model Training & Evaluation")

selected_configs = st.sidebar.multiselect(
    "Select configurations to train and evaluate",
    list(configs.keys()),
    default=list(configs.keys())
)

test_file = st.sidebar.text_input("Test file path", "tests/test_data.yml")
train_button = st.sidebar.button("Train & Evaluate Selected Models")

# Main content area for displaying results
main_tab, details_tab = st.tabs(["Results Summary", "Detailed Results"])

# Function to train a model with a specific configuration
def train_model(config_file):
    output_path = f"models/{os.path.basename(config_file).replace('.yml', '')}"
    try:
        model_path = train(
            domain="domain.yml",
            config=config_file,
            training_files="data/train",
            output=output_path,
            fixed_model_name=os.path.basename(config_file).replace('.yml', '')
        )
        return model_path
    except Exception as e:
        st.error(f"Error training model with {config_file}: {str(e)}")
        return None

# Function to evaluate a model
def evaluate_model(model_path, test_file):
    try:
        # Extract just the string path if it's a training result object
        if not isinstance(model_path, str):
            if hasattr(model_path, 'model'):
                model_path = model_path.model
            else:
                st.error(f"Invalid model path: {model_path}")
                return None
                
        output = subprocess.check_output(
            f"rasa test nlu --model {model_path} --nlu {test_file} --out results",
            shell=True
        )
        
        # Load the results
        results_file = f"results/intent_report.json"
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return results
    except Exception as e:
        st.error(f"Error evaluating model {model_path}: {str(e)}")
        return None

# Function to parse results
def parse_results(results):
    if not results:
        return None
    
    # Extract overall metrics
    overall = results.get('weighted avg', {})
    
    metrics = {
        'precision': overall.get('precision', 0),
        'recall': overall.get('recall', 0),
        'f1-score': overall.get('f1-score', 0),
        'support': overall.get('support', 0),
    }
    
    return metrics

if train_button:
    results = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, config_name in enumerate(selected_configs):
        config_file = configs[config_name]
        status_text.text(f"Training model with {config_name}...")
        
        # Train the model
        model_path = train_model(config_file)
        
        if model_path:
            status_text.text(f"Evaluating model {config_name}...")
            # Evaluate the model
            eval_results = evaluate_model(model_path, test_file)
            metrics = parse_results(eval_results)
            
            if metrics:
                results[config_name] = metrics
        
        progress_bar.progress((i + 1) / len(selected_configs))
    
    status_text.text("Training and evaluation complete!")
    
    # Display results in the main tab
    with main_tab:
        if results:
            # Convert results to DataFrame for easy display
            df = pd.DataFrame(results).T
            df = df.sort_values('f1-score', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Metrics Comparison")
                st.dataframe(df.style.highlight_max(axis=0, color='lightgreen'))
            
            with col2:
                st.subheader("F1-Score Comparison")
                fig, ax = plt.subplots()
                df['f1-score'].plot(kind='bar', ax=ax)
                ax.set_ylabel('F1-Score')
                ax.set_title('Model F1-Score Comparison')
                st.pyplot(fig)
        else:
            st.warning("No results to display. Training or evaluation may have failed.")
    
    # Detailed results in the details tab
    with details_tab:
        for config_name in results:
            st.subheader(f"{config_name} Details")
            st.json(results[config_name])
            
            # Try to load the confusion matrix
            cm_path = f"results/confmat.png"
            if os.path.exists(cm_path):
                st.image(cm_path, caption=f"Confusion Matrix for {config_name}")

# Display information about the configurations
st.sidebar.header("Configuration Details")
st.sidebar.markdown("""
- **Config_1**: Sparse features + LaBSE (109+ languages)
- **Config_1_b**: Sparse features + AfroXLMR (African languages)
- **Config_2**: Dense features from XLM-RoBERTa
- **Config_2_b**: Dense features from AfriMT5 (African languages)
- **Config_3**: Sparse features only (lightest model)
""")

# Display information about how to create test data
st.sidebar.header("Test Data")
st.sidebar.markdown("""
Make sure you have test data in the Rasa NLU YAML format:
```yaml
version: "3.1"
nlu:
- intent: intent_name
  examples: |
    - example 1
    - example 2
```
""")

# Instructions for running with different configs
st.sidebar.header("Running Individual Models")
st.sidebar.markdown("""
To train a model with a specific config:
```bash
rasa train --config config_1.yml
```

To run the bot with a specific model:
```bash
rasa shell --model models/config_1
```
""")

# Add a section to create test data if it doesn't exist
if not os.path.exists(test_file):
    st.warning(f"Test file '{test_file}' not found. Create a test file first.")
    
    st.header("Create Test Data")
    test_data_content = st.text_area(
        "Enter test data in Rasa YAML format",
        """version: "3.1"
nlu:
- intent: greeting
  examples: |
    - hello
    - hi
    - hey
""",
        height=300
    )
    
    if st.button("Save Test Data"):
        test_dir = os.path.dirname(test_file)
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            
        with open(test_file, 'w') as f:
            f.write(test_data_content)
        
        st.success(f"Test data saved to {test_file}") 