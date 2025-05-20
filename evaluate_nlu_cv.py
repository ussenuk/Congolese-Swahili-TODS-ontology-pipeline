#!/usr/bin/env python3
"""
NLU Model Evaluation with 5-Fold Cross-Validation

This script evaluates the NLU model's performance on intent recognition and entity extraction
using 5-fold cross-validation to ensure a fair assessment despite limited data.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
import yaml
import subprocess
import tempfile
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Force CPU-only execution
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

def load_nlu_data(nlu_file):
    """Load NLU data from YAML file"""
    with open(nlu_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data

def split_nlu_data(data, train_indices, test_indices):
    """Split NLU data into training and testing sets based on indices"""
    train_data = {"version": data.get("version", "3.1"), "nlu": []}
    test_data = {"version": data.get("version", "3.1"), "nlu": []}
    
    for idx, intent_data in enumerate(data.get("nlu", [])):
        if idx in train_indices:
            train_data["nlu"].append(intent_data)
        elif idx in test_indices:
            test_data["nlu"].append(intent_data)
    
    return train_data, test_data

def write_yaml(data, file_path):
    """Write data to YAML file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    logger.info(f"Wrote data to {file_path}")

def run_rasa_train(config_file, train_file, output_dir):
    """Train a Rasa model with the specified config and training data"""
    model_name = f"nlu-model-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    command = [
        "rasa", "train", "nlu",
        "--config", config_file,
        "--nlu", train_file,
        "--out", output_dir,
        "--fixed-model-name", model_name
    ]
    
    logger.info(f"Training model with command: {' '.join(command)}")
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "-1"
    subprocess.run(command, check=True, env=env)
    
    return os.path.join(output_dir, f"{model_name}.tar.gz")

def run_rasa_test(model_path, test_file):
    """Test a Rasa model on the test data and return the results directory"""
    results_dir = tempfile.mkdtemp()
    command = [
        "rasa", "test", "nlu",
        "--model", model_path,
        "--nlu", test_file,
        "--out", results_dir
    ]
    
    logger.info(f"Testing model with command: {' '.join(command)}")
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "-1"
    subprocess.run(command, check=True, env=env)
    
    # Return the directory containing the results
    return results_dir

def extract_metrics(results_dir):
    """
    Extract metrics from Rasa test results
    
    Args:
        results_dir: Directory with test results
        
    Returns:
        Tuple of (intent_metrics, entity_metrics)
    """
    # Read intent report
    intent_report_path = os.path.join(results_dir, "intent_report.json")
    entity_report_path = os.path.join(results_dir, "DIETClassifier_report.json")
    
    intent_metrics = {}
    entity_metrics = {}
    
    if os.path.exists(intent_report_path):
        with open(intent_report_path, 'r') as f:
            intent_report = json.load(f)
            
        # Log intent report structure for debugging - fix JSON serialization error
        logger.debug(f"Intent report keys: {list(intent_report.keys())}")
        
        # Extract weighted average metrics (overall performance)
        if "weighted avg" in intent_report:
            weighted_avg = intent_report["weighted avg"]
            intent_metrics = {
                "precision": weighted_avg.get("precision", 0.0),
                "recall": weighted_avg.get("recall", 0.0),
                "f1-score": weighted_avg.get("f1-score", 0.0),
                "support": weighted_avg.get("support", 0)
            }
        else:
            logger.warning("No 'weighted avg' found in intent report. Using zeros for metrics.")
            intent_metrics = {
                "precision": 0.0,
                "recall": 0.0,
                "f1-score": 0.0,
                "support": 0
            }
    else:
        logger.warning(f"Intent report not found at {intent_report_path}")
        intent_metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1-score": 0.0,
            "support": 0
        }
    
    # Read entity report
    if os.path.exists(entity_report_path):
        with open(entity_report_path, 'r') as f:
            entity_report = json.load(f)
            
        # Extract weighted average metrics for entities
        if "weighted avg" in entity_report:
            weighted_avg = entity_report["weighted avg"]
            entity_metrics = {
                "precision": weighted_avg.get("precision", 0.0),
                "recall": weighted_avg.get("recall", 0.0),
                "f1-score": weighted_avg.get("f1-score", 0.0),
                "support": weighted_avg.get("support", 0)
            }
        else:
            logger.warning("No 'weighted avg' found in entity report. Using zeros for metrics.")
            entity_metrics = {
                "precision": 0.0,
                "recall": 0.0,
                "f1-score": 0.0,
                "support": 0
            }
    else:
        logger.warning(f"Entity report not found at {entity_report_path}")
        entity_metrics = {
            "precision": 0.0,
            "recall": 0.0,
            "f1-score": 0.0,
            "support": 0
        }
    
    return intent_metrics, entity_metrics

def run_cross_validation(nlu_file, config_file, n_splits=5):
    """Run k-fold cross-validation for NLU model evaluation"""
    # Load NLU data
    data = load_nlu_data(nlu_file)
    n_intents = len(data.get("nlu", []))
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    models_dir = os.path.join(temp_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # Create indices for cross-validation
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    all_indices = np.arange(n_intents)
    
    # Initialize metrics storage
    intent_metrics_list = []
    entity_metrics_list = []
    
    # Run cross-validation
    for fold, (train_idx, test_idx) in enumerate(kf.split(all_indices)):
        logger.info(f"Starting fold {fold+1}/{n_splits}")
        
        # Create train/test split
        train_data, test_data = split_nlu_data(data, train_idx, test_idx)
        
        # Write split files
        train_file = os.path.join(temp_dir, f"train_fold_{fold+1}.yml")
        test_file = os.path.join(temp_dir, f"test_fold_{fold+1}.yml")
        write_yaml(train_data, train_file)
        write_yaml(test_data, test_file)
        
        # Train model
        model_path = run_rasa_train(config_file, train_file, models_dir)
        
        # Test model and get results directory
        results_dir = run_rasa_test(model_path, test_file)
        
        # Extract metrics from the results directory
        intent_metrics, entity_metrics = extract_metrics(results_dir)
        intent_metrics_list.append(intent_metrics)
        entity_metrics_list.append(entity_metrics)
        
        logger.info(f"Fold {fold+1} intent metrics: {intent_metrics}")
        logger.info(f"Fold {fold+1} entity metrics: {entity_metrics}")
    
    # Calculate average metrics
    avg_intent_metrics = {
        "precision": np.mean([m["precision"] for m in intent_metrics_list]),
        "recall": np.mean([m["recall"] for m in intent_metrics_list]),
        "f1-score": np.mean([m["f1-score"] for m in intent_metrics_list]),
        "support": np.mean([m["support"] for m in intent_metrics_list])
    }
    
    avg_entity_metrics = {
        "precision": np.mean([m["precision"] for m in entity_metrics_list]),
        "recall": np.mean([m["recall"] for m in entity_metrics_list]),
        "f1-score": np.mean([m["f1-score"] for m in entity_metrics_list]),
        "support": np.mean([m["support"] for m in entity_metrics_list])
    }
    
    # Create detailed report
    report = {
        "intent_evaluation": {
            "per_fold": intent_metrics_list,
            "average": avg_intent_metrics
        },
        "entity_evaluation": {
            "per_fold": entity_metrics_list,
            "average": avg_entity_metrics
        }
    }
    
    # Write report
    report_file = f"nlu_cv_evaluation_report_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Cross-validation complete. Report saved to {report_file}")
    
    # Print summary
    print("\n" + "="*50)
    print("CROSS-VALIDATION RESULTS SUMMARY")
    print("="*50)
    print("\nIntent Recognition:")
    print(f"  Precision: {avg_intent_metrics['precision']:.4f}")
    print(f"  Recall: {avg_intent_metrics['recall']:.4f}")
    print(f"  F1-score: {avg_intent_metrics['f1-score']:.4f}")
    print(f"  Support: {avg_intent_metrics['support']:.4f}")
    
    print("\nEntity Extraction:")
    print(f"  Precision: {avg_entity_metrics['precision']:.4f}")
    print(f"  Recall: {avg_entity_metrics['recall']:.4f}")
    print(f"  F1-score: {avg_entity_metrics['f1-score']:.4f}")
    print(f"  Support: {avg_entity_metrics['support']:.4f}")
    print("\n" + "="*50)
    
    return report

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate NLU model with 5-fold cross-validation")
    parser.add_argument("--nlu", required=True, help="Path to NLU data file (YAML)")
    parser.add_argument("--config", required=True, help="Path to config file")
    parser.add_argument("--folds", type=int, default=5, help="Number of folds for cross-validation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Log that we're using CPU-only mode
    logger.info("Running in CPU-only mode (CUDA_VISIBLE_DEVICES=-1)")
    
    run_cross_validation(args.nlu, args.config, args.folds) 