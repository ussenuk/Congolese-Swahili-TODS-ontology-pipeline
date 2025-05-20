#!/usr/bin/env python3
"""
Ontology Pipeline Evaluation

This script implements the evaluation methodology described in the paper for assessing
an ontology-based dialogue system. It calculates:

1. Task Completion Rate: Ratio of successful tasks to total attempted tasks
2. Task Completion Cost: Average number of dialogue turns needed to complete a task
3. Edit Distance: Measure of how much the actual dialogue deviates from an ideal dialogue

Usage:
    python evaluate_ontology_pipeline.py --input dialogues.json --output results.json
"""

import os
import sys
import json
import argparse
import logging
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class OntologyPipelineEvaluator:
    """Evaluator for ontology pipeline performance based on dialogue tasks"""
    
    def __init__(self, dialogues_path: str):
        """
        Initialize the evaluator with dialogues data
        
        Args:
            dialogues_path: Path to the JSON file containing annotated dialogues
        """
        self.dialogues = self._load_dialogues(dialogues_path)
        
        # Define possible task types - customize these based on your ontology domain
        self.task_types = [
            "provide_information",
            "answer_query",
            "provide_entity_details", 
            "list_entities",
            "explain_relationship",
            "other"
        ]
        
        self.metrics = {}
    
    def _load_dialogues(self, dialogues_path: str) -> List[Dict[str, Any]]:
        """Load dialogues from JSON file"""
        try:
            with open(dialogues_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract dialogues list from the JSON data
            if isinstance(data, dict) and "dialogues" in data:
                dialogues = data["dialogues"]
            else:
                dialogues = data  # Assume the entire JSON is the dialogues list
                
            logger.info(f"Loaded {len(dialogues)} dialogues from {dialogues_path}")
            return dialogues
        except Exception as e:
            logger.error(f"Failed to load dialogues from {dialogues_path}: {e}")
            return []
    
    def calculate_task_completion_rate(self) -> Dict[str, float]:
        """
        Calculate task completion rate for all dialogues
        
        Returns:
            Dictionary with task completion rates by task type and overall
        """
        task_success = defaultdict(int)
        task_attempts = defaultdict(int)
        
        # Process each dialogue
        for dialogue in self.dialogues:
            # Extract tasks from dialogue
            for turn in dialogue.get("turns", []):
                if "tasks" not in turn:
                    continue
                
                for task in turn.get("tasks", []):
                    task_type = task.get("type")
                    if task_type not in self.task_types:
                        continue
                    
                    task_attempts[task_type] += 1
                    task_attempts["overall"] += 1
                    
                    if task.get("success", False):
                        task_success[task_type] += 1
                        task_success["overall"] += 1
        
        # Calculate completion rates
        completion_rates = {}
        for task_type in self.task_types + ["overall"]:
            if task_attempts[task_type] > 0:
                completion_rates[task_type] = task_success[task_type] / task_attempts[task_type]
            else:
                completion_rates[task_type] = 0.0
        
        logger.info(f"Task completion rates: {completion_rates}")
        self.metrics["task_completion_rate"] = completion_rates
        return completion_rates
    
    def calculate_task_completion_cost(self) -> Dict[str, float]:
        """
        Calculate task completion cost (average turns per task)
        
        Returns:
            Dictionary with task completion costs by task type and overall
        """
        task_turns = defaultdict(list)
        
        # Process each dialogue
        for dialogue in self.dialogues:
            # Track tasks and turns per task
            task_turn_count = defaultdict(int)
            active_tasks = defaultdict(set)
            
            for turn_idx, turn in enumerate(dialogue.get("turns", [])):
                # Register new tasks that start in this turn
                for task in turn.get("tasks", []):
                    task_type = task.get("type")
                    task_id = task.get("id")
                    if task_type not in self.task_types:
                        continue
                    
                    active_tasks[task_type].add(task_id)
                    task_turn_count[(task_type, task_id)] = 1
                
                # Check for tasks that complete in this turn
                for task in turn.get("tasks", []):
                    task_type = task.get("type")
                    task_id = task.get("id")
                    if task_type not in self.task_types:
                        continue
                    
                    if task.get("success", False) and task_id in active_tasks[task_type]:
                        # Task completed successfully
                        task_turns[task_type].append(task_turn_count[(task_type, task_id)])
                        task_turns["overall"].append(task_turn_count[(task_type, task_id)])
                        active_tasks[task_type].remove(task_id)
                
                # Increment turn count for active tasks
                for task_type in self.task_types:
                    for task_id in active_tasks[task_type]:
                        task_turn_count[(task_type, task_id)] += 1
        
        # Calculate average turn counts
        completion_costs = {}
        for task_type in self.task_types + ["overall"]:
            if task_turns[task_type]:
                completion_costs[task_type] = np.mean(task_turns[task_type])
            else:
                completion_costs[task_type] = 0.0
        
        logger.info(f"Task completion costs: {completion_costs}")
        self.metrics["task_completion_cost"] = completion_costs
        return completion_costs
    
    def calculate_edit_distance(self) -> Dict[str, float]:
        """
        Calculate edit distance between actual and ideal dialogues
        Based on the formula: Error = (substitutions + deletions + 0.4 * insertions) / ground_truth_turns
        
        Returns:
            Dictionary with edit distance metrics
        """
        edit_distances = []
        
        for dialogue in self.dialogues:
            # Get ground truth and actual dialogue turns
            ground_truth = dialogue.get("ground_truth_turns", [])
            actual = dialogue.get("turns", [])
            
            if not ground_truth or not actual:
                continue
            
            # Count substitutions, deletions, and insertions
            substitutions = 0
            deletions = 0
            insertions = 0
            
            for turn in actual:
                if turn.get("error_type") == "substitution":
                    substitutions += 1
                elif turn.get("error_type") == "deletion":
                    deletions += 1
                elif turn.get("error_type") == "insertion":
                    insertions += 1
            
            # Calculate error rate using the formula from the paper
            if len(ground_truth) > 0:
                error_rate = (substitutions + deletions + 0.4 * insertions) / len(ground_truth)
                edit_distances.append(error_rate)
        
        edit_distance_metrics = {
            "mean_edit_distance": np.mean(edit_distances) if edit_distances else 0.0,
            "median_edit_distance": np.median(edit_distances) if edit_distances else 0.0,
            "min_edit_distance": min(edit_distances) if edit_distances else 0.0,
            "max_edit_distance": max(edit_distances) if edit_distances else 0.0
        }
        
        logger.info(f"Edit distance metrics: {edit_distance_metrics}")
        self.metrics["edit_distance"] = edit_distance_metrics
        return edit_distance_metrics
    
    def evaluate_all_metrics(self) -> Dict[str, Any]:
        """
        Calculate all metrics and return combined results
        
        Returns:
            Dictionary with all metrics
        """
        self.calculate_task_completion_rate()
        self.calculate_task_completion_cost()
        self.calculate_edit_distance()
        
        return self.metrics
    
    def save_metrics(self, output_file: str) -> None:
        """
        Save metrics to a JSON file
        
        Args:
            output_file: Path to save the metrics
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2)
        logger.info(f"Saved metrics to {output_file}")

def create_dialogue_annotation_template(output_path: str) -> None:
    """
    Create a template file for annotating dialogues
    
    Args:
        output_path: Path to save the template
    """
    template = {
        "version": "1.0",
        "instructions": """
            This file serves as a template for annotating dialogues for evaluation.
            For each dialogue, add turns and annotate them with tasks and error types.
            
            For each bot turn, add one or more tasks with the following properties:
            - id: A unique identifier for the task
            - type: One of the predefined task types
            - success: Boolean indicating if the task was successful
            
            For error types, use:
            - substitution: Wrong information or answer
            - deletion: Missing information
            - insertion: Irrelevant or redundant information
            
            Also add ground_truth_turns to represent the ideal dialogue.
        """,
        "dialogues": [
            {
                "id": "dialogue_1",
                "turns": [
                    {
                        "id": "turn_1",
                        "speaker": "user",
                        "text": "User: What facilities are available in Camp A?"
                    },
                    {
                        "id": "turn_2",
                        "speaker": "bot",
                        "text": "Bot: Camp A has 3 water points, 1 health facility, and 2 food distribution centers.",
                        "tasks": [
                            {
                                "id": "task_1",
                                "type": "list_entities",
                                "success": True
                            }
                        ]
                    }
                ],
                "ground_truth_turns": [
                    {
                        "id": "gt_turn_1",
                        "speaker": "user",
                        "text": "User: What facilities are available in Camp A?"
                    },
                    {
                        "id": "gt_turn_2",
                        "speaker": "bot",
                        "text": "Bot: Camp A has 3 water points, 1 health facility, and 2 food distribution centers."
                    }
                ]
            }
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    logger.info(f"Created dialogue annotation template at {output_path}")

def convert_raw_dialogues(input_file: str, output_file: str) -> None:
    """
    Convert raw dialogue text to the structured JSON format needed for evaluation
    
    Args:
        input_file: Path to raw dialogue file (text)
        output_file: Path to save structured dialogues (JSON)
    """
    dialogues = []
    current_dialogue = None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Simple parsing logic - assumes dialogues are separated by blank lines
        # and turns are in format "User: ..." or "Bot: ..."
        for line in lines:
            line = line.strip()
            
            if not line:
                # End of dialogue
                if current_dialogue and current_dialogue.get("turns"):
                    dialogues.append(current_dialogue)
                current_dialogue = {"id": f"dialogue_{len(dialogues)+1}", "turns": []}
                continue
            
            if not current_dialogue:
                current_dialogue = {"id": f"dialogue_{len(dialogues)+1}", "turns": []}
            
            # Check if line starts with User: or Bot:
            if line.startswith("User:") or line.startswith("Bot:"):
                speaker = "user" if line.startswith("User:") else "bot"
                content = line[5:].strip() if speaker == "user" else line[4:].strip()
                
                turn = {
                    "id": f"turn_{len(current_dialogue['turns'])+1}",
                    "speaker": speaker,
                    "text": line,
                    "content": content
                }
                current_dialogue["turns"].append(turn)
        
        # Add the last dialogue
        if current_dialogue and current_dialogue.get("turns"):
            dialogues.append(current_dialogue)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"dialogues": dialogues}, f, indent=2)
        
        logger.info(f"Converted {len(dialogues)} dialogues from {input_file} to {output_file}")
        
    except Exception as e:
        logger.error(f"Failed to convert dialogues: {e}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate ontology pipeline based on dialogues")
    parser.add_argument("--input", required=True, help="Path to annotated dialogues JSON file")
    parser.add_argument("--output", default="evaluation_results.json", help="Path to save evaluation results")
    parser.add_argument("--create-template", action="store_true", help="Create annotation template file")
    parser.add_argument("--template-output", default="dialogue_template.json", help="Path to save template file")
    parser.add_argument("--convert", help="Path to raw dialogues text file to convert")
    parser.add_argument("--convert-output", default="converted_dialogues.json", help="Path to save converted dialogues")
    
    args = parser.parse_args()
    
    if args.create_template:
        create_dialogue_annotation_template(args.template_output)
        return
    
    if args.convert:
        convert_raw_dialogues(args.convert, args.convert_output)
        return
    
    evaluator = OntologyPipelineEvaluator(args.input)
    evaluator.evaluate_all_metrics()
    evaluator.save_metrics(args.output)

if __name__ == "__main__":
    main() 