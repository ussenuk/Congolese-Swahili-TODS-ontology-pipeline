#!/usr/bin/env python3
"""
Task-Based Evaluation Metrics

This script implements the task completion rate and task completion cost metrics
for evaluating the effectiveness of the conversational agent in humanitarian response scenarios.
It processes manually annotated dialogue data to calculate:

1. Task Completion Rate: Ratio of successful tasks to total attempted tasks
2. Task Completion Cost: Average number of dialogue turns needed to complete a task

As described in Section 3.4 (Evaluation) of the paper.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import logging
import argparse
from collections import defaultdict
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class DialogueEvaluator:
    """Evaluator for task completion metrics on humanitarian response dialogues"""
    
    def __init__(self, dialogues_path: str):
        """
        Initialize the evaluator with dialogues data
        
        Args:
            dialogues_path: Path to the JSON file containing annotated dialogues
        """
        self.dialogues = self._load_dialogues(dialogues_path)
        self.task_types = [
            "provide_guideline",
            "provide_guideline_detail",
            "provide_guideline_step",
            "provide_specific_handling"
        ]
        self.metrics = {}
    
    def _load_dialogues(self, dialogues_path: str) -> List[Dict[str, Any]]:
        """Load dialogues from JSON file"""
        try:
            with open(dialogues_path, 'r', encoding='utf-8') as f:
                dialogues = json.load(f)
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
            
            # Simple implementation of edit distance calculation
            # This is a simplified version - a real implementation would use 
            # a proper edit distance algorithm
            for i, turn in enumerate(actual):
                if turn.get("error_type") == "substitution":
                    substitutions += 1
                elif turn.get("error_type") == "deletion":
                    deletions += 1
                elif turn.get("error_type") == "insertion":
                    insertions += 1
            
            # Calculate error rate using the formula from the paper
            if len(actual) > 0:
                error_rate = (substitutions + deletions + 0.4 * insertions) / len(actual)
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

def create_sample_dialogue_data(output_path: str, num_dialogues: int = 5) -> None:
    """
    Create a sample dialogue data file for testing
    
    Args:
        output_path: Path to save the sample data
        num_dialogues: Number of sample dialogues to create
    """
    dialogues = []
    
    task_types = [
        "provide_guideline",
        "provide_guideline_detail",
        "provide_guideline_step",
        "provide_specific_handling"
    ]
    
    for dialogue_id in range(num_dialogues):
        turns = []
        num_turns = np.random.randint(3, 8)
        
        for turn_id in range(num_turns):
            tasks = []
            num_tasks = np.random.randint(0, 3)
            
            for task_id in range(num_tasks):
                task_type = np.random.choice(task_types)
                success = np.random.choice([True, False], p=[0.7, 0.3])
                
                tasks.append({
                    "id": f"task_{dialogue_id}_{turn_id}_{task_id}",
                    "type": task_type,
                    "success": success
                })
            
            # Randomly assign error types
            error_type = np.random.choice(
                [None, "substitution", "deletion", "insertion"], 
                p=[0.7, 0.1, 0.1, 0.1]
            )
            
            turns.append({
                "id": f"turn_{dialogue_id}_{turn_id}",
                "text": f"Sample turn {turn_id} in dialogue {dialogue_id}",
                "tasks": tasks,
                "error_type": error_type
            })
        
        # Create ideal ground truth turns (simplified)
        ground_truth_turns = [turn for turn in turns if turn.get("error_type") is None]
        
        dialogues.append({
            "id": f"dialogue_{dialogue_id}",
            "turns": turns,
            "ground_truth_turns": ground_truth_turns
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, indent=2)
    
    logger.info(f"Created sample dialogue data with {num_dialogues} dialogues at {output_path}")

def create_dialogue_annotation_template(output_path: str) -> None:
    """
    Create a template file for dialogue annotation
    
    Args:
        output_path: Path to save the template
    """
    template = {
        "instructions": """
        Dialogue Annotation Instructions:
        
        1. For each dialogue turn, identify all tasks being attempted
        2. Mark each task with:
           - type: One of "provide_guideline", "provide_guideline_detail", "provide_guideline_step", "provide_specific_handling"
           - success: true/false depending on whether the task was completed successfully
        3. Mark error types for turns:
           - substitution: System failed to execute a task
           - deletion: System offered no response
           - insertion: User had to repeat their query
        4. Create a ground_truth_turns array with the ideal sequence of turns
        """,
        "template_dialogue": {
            "id": "dialogue_1",
            "turns": [
                {
                    "id": "turn_1",
                    "text": "User: What should I do in case of flood?",
                    "tasks": [
                        {
                            "id": "task_1",
                            "type": "provide_guideline",
                            "success": True
                        }
                    ],
                    "error_type": None
                },
                {
                    "id": "turn_2",
                    "text": "Bot: What step should I take first?",
                    "tasks": [
                        {
                            "id": "task_2",
                            "type": "provide_guideline_step",
                            "success": False
                        }
                    ],
                    "error_type": "substitution"
                }
            ],
            "ground_truth_turns": [
                {
                    "id": "ideal_turn_1",
                    "text": "User: What should I do in case of flood?"
                },
                {
                    "id": "ideal_turn_2",
                    "text": "Bot: In case of flood, first move to higher ground, then..."
                }
            ]
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2)
    
    logger.info(f"Created dialogue annotation template at {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate task-based metrics for dialogue system")
    
    parser.add_argument("--dialogues", type=str, help="Path to annotated dialogues JSON file")
    parser.add_argument("--output", type=str, default="task_metrics.json", help="Path to save metrics results")
    parser.add_argument("--create-sample", action="store_true", help="Create sample dialogue data")
    parser.add_argument("--create-template", action="store_true", help="Create dialogue annotation template")
    parser.add_argument("--sample-output", type=str, default="sample_dialogues.json", help="Path to save sample data")
    parser.add_argument("--template-output", type=str, default="dialogue_annotation_template.json", 
                       help="Path to save annotation template")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_dialogue_data(args.sample_output)
        sys.exit(0)
    
    if args.create_template:
        create_dialogue_annotation_template(args.template_output)
        sys.exit(0)
    
    if not args.dialogues:
        parser.error("Please provide path to dialogues with --dialogues or use --create-sample to create sample data")
    
    evaluator = DialogueEvaluator(args.dialogues)
    metrics = evaluator.evaluate_all_metrics()
    evaluator.save_metrics(args.output)
    
    # Print summary
    print("\n" + "="*50)
    print("TASK-BASED EVALUATION METRICS")
    print("="*50)
    
    print("\nTask Completion Rate:")
    for task_type, rate in metrics["task_completion_rate"].items():
        print(f"  {task_type}: {rate:.4f}")
    
    print("\nTask Completion Cost (Average Turns):")
    for task_type, cost in metrics["task_completion_cost"].items():
        print(f"  {task_type}: {cost:.4f}")
    
    if "edit_distance" in metrics:
        print("\nEdit Distance Metrics:")
        for metric, value in metrics["edit_distance"].items():
            print(f"  {metric}: {value:.4f}")
    
    print("\n" + "="*50) 