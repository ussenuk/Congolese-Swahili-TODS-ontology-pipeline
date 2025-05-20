#!/usr/bin/env python3
"""
Interactive Dialogue Annotation Tool

This script provides a command-line interface for annotating dialogues with task information
and error types. It allows users to manually mark which tasks were successfully completed,
identify errors, and define ground truth dialogues.

Usage:
    python annotate_dialogues.py --input raw_dialogues.txt --output annotated_dialogues.json
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define task types for ontology-based systems
TASK_TYPES = [
    "provide_information",
    "answer_query",
    "provide_entity_details", 
    "list_entities",
    "explain_relationship",
    "other"
]

# Define error types
ERROR_TYPES = [None, "substitution", "deletion", "insertion"]

def load_raw_dialogues(input_file: str) -> List[Dict[str, Any]]:
    """
    Load raw dialogues from a text file
    
    Args:
        input_file: Path to raw dialogue file
    
    Returns:
        List of parsed dialogues
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
        
        logger.info(f"Loaded {len(dialogues)} raw dialogues from {input_file}")
        return dialogues
    
    except Exception as e:
        logger.error(f"Failed to load raw dialogues from {input_file}: {e}")
        return []

def annotate_dialogues_interactive(dialogues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Interactively annotate dialogues with task and error information
    
    Args:
        dialogues: List of raw dialogues
    
    Returns:
        List of annotated dialogues
    """
    annotated_dialogues = []
    
    print("\n" + "="*50)
    print("DIALOGUE ANNOTATION TOOL FOR ONTOLOGY PIPELINE EVALUATION")
    print("="*50)
    print("\nTask types:")
    for i, task_type in enumerate(TASK_TYPES, 1):
        print(f"  {i}. {task_type}")
    
    print("\nError types:")
    for i, error_type in enumerate(ERROR_TYPES, 0):
        print(f"  {i}. {error_type if error_type else 'None'}")
    
    for dialogue_idx, dialogue in enumerate(dialogues, 1):
        print("\n" + "="*50)
        print(f"DIALOGUE {dialogue_idx}/{len(dialogues)}: {dialogue['id']}")
        print("="*50)
        
        # Print dialogue for reference
        for i, turn in enumerate(dialogue.get("turns", []), 1):
            print(f"{i}. {turn.get('text', '')}")
        
        # Create a copy with annotated turns
        annotated_dialogue = {
            "id": dialogue["id"],
            "turns": [],
            "ground_truth_turns": []
        }
        
        # Process each turn
        for i, turn in enumerate(dialogue.get("turns", []), 1):
            print("\n" + "-"*30)
            print(f"Turn {i}: {turn.get('text', '')}")
            
            # Create annotated turn
            annotated_turn = {
                "id": turn["id"],
                "text": turn.get("text", ""),
                "speaker": turn.get("speaker", ""),
                "content": turn.get("content", ""),
                "tasks": []
            }
            
            # Only ask for tasks and errors for bot turns
            if turn.get("speaker") == "bot":
                # Ask for tasks
                while True:
                    try:
                        num_tasks = input(f"Number of tasks in this turn (0-5) [0]: ")
                        num_tasks = int(num_tasks) if num_tasks.strip() else 0
                        if 0 <= num_tasks <= 5:
                            break
                        print("Please enter a number between 0 and 5")
                    except ValueError:
                        print("Please enter a valid number")
                
                # Get task details
                for j in range(num_tasks):
                    task = {"id": f"task_{turn['id']}_{j+1}"}
                    
                    # Get task type
                    while True:
                        try:
                            print("\nTask types:")
                            for k, task_type in enumerate(TASK_TYPES, 1):
                                print(f"  {k}. {task_type}")
                            
                            type_idx = input(f"Task {j+1} type (1-{len(TASK_TYPES)}): ")
                            type_idx = int(type_idx) - 1
                            if 0 <= type_idx < len(TASK_TYPES):
                                task["type"] = TASK_TYPES[type_idx]
                                break
                            print(f"Please enter a number between 1 and {len(TASK_TYPES)}")
                        except ValueError:
                            print("Please enter a valid number")
                    
                    # Get success status
                    while True:
                        success = input(f"Was task {j+1} successful? (y/n) [y]: ").lower()
                        if success in ("", "y", "yes"):
                            task["success"] = True
                            break
                        elif success in ("n", "no"):
                            task["success"] = False
                            break
                        print("Please enter 'y' or 'n'")
                    
                    annotated_turn["tasks"].append(task)
                
                # Get error type
                while True:
                    try:
                        print("\nError types:")
                        for k, error_type in enumerate(ERROR_TYPES, 0):
                            print(f"  {k}. {error_type if error_type else 'None'}")
                        
                        error_idx = input(f"Error type (0-{len(ERROR_TYPES)-1}) [0]: ")
                        error_idx = int(error_idx) if error_idx.strip() else 0
                        if 0 <= error_idx < len(ERROR_TYPES):
                            error_type = ERROR_TYPES[error_idx]
                            if error_type:
                                annotated_turn["error_type"] = error_type
                            break
                        print(f"Please enter a number between 0 and {len(ERROR_TYPES)-1}")
                    except ValueError:
                        print("Please enter a valid number")
            
            annotated_dialogue["turns"].append(annotated_turn)
        
        # Ask for ground truth turns
        print("\n" + "-"*30)
        print("Now let's define the ground truth turns (ideal dialogue)")
        print("For each bot turn, indicate if it should be different in the ideal case")
        
        # Start with user turns and ask for bot turn corrections
        ground_truth = []
        for turn in annotated_dialogue["turns"]:
            if turn.get("speaker") == "user":
                # User turns stay the same
                ground_truth.append({
                    "id": f"gt_{turn['id']}",
                    "speaker": "user",
                    "text": turn.get("text", ""),
                    "content": turn.get("content", "")
                })
            else:
                # For bot turns, ask if they need correction
                print("\n" + "-"*30)
                print(f"Bot turn: {turn.get('text', '')}")
                
                while True:
                    needs_correction = input("Does this turn need correction in the ideal dialogue? (y/n) [n]: ").lower()
                    if needs_correction in ("", "n", "no"):
                        # Keep original
                        ground_truth.append({
                            "id": f"gt_{turn['id']}",
                            "speaker": "bot",
                            "text": turn.get("text", ""),
                            "content": turn.get("content", "")
                        })
                        break
                    elif needs_correction in ("y", "yes"):
                        # Get corrected text
                        corrected_text = input("Enter the ideal bot response: ")
                        ground_truth.append({
                            "id": f"gt_{turn['id']}",
                            "speaker": "bot",
                            "text": f"Bot: {corrected_text}",
                            "content": corrected_text
                        })
                        break
                    print("Please enter 'y' or 'n'")
        
        annotated_dialogue["ground_truth_turns"] = ground_truth
        annotated_dialogues.append(annotated_dialogue)
        
        print("\nDialogue annotation complete!")
        
        # Ask if the user wants to continue with the next dialogue
        if dialogue_idx < len(dialogues):
            while True:
                continue_annotation = input("Continue with next dialogue? (y/n) [y]: ").lower()
                if continue_annotation in ("", "y", "yes"):
                    break
                elif continue_annotation in ("n", "no"):
                    print("Annotation stopped by user")
                    return annotated_dialogues
                print("Please enter 'y' or 'n'")
    
    return annotated_dialogues

def save_annotated_dialogues(dialogues: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save annotated dialogues to a JSON file
    
    Args:
        dialogues: List of annotated dialogues
        output_file: Path to save the annotated dialogues
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"dialogues": dialogues}, f, indent=2)
        logger.info(f"Saved {len(dialogues)} annotated dialogues to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save annotated dialogues to {output_file}: {e}")

def create_sample_raw_dialogues(output_file: str, num_dialogues: int = 2) -> None:
    """
    Create a sample raw dialogues file for testing
    
    Args:
        output_file: Path to save the sample data
        num_dialogues: Number of sample dialogues to create
    """
    sample_dialogues = [
        [
            "User: What facilities are available in Camp A?",
            "Bot: Camp A has 3 water points, 1 health facility, and 2 food distribution centers.",
            "User: How many people can the health facility serve?",
            "Bot: The health facility in Camp A can serve approximately 500 people per day."
        ],
        [
            "User: Where can I find water in Sector B?",
            "Bot: There are 2 water points in Sector B: one at the north entrance and one near the community center.",
            "User: Is the water safe to drink?",
            "Bot: Yes, all water points are treated and tested regularly for safety."
        ]
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, dialogue in enumerate(sample_dialogues[:num_dialogues], 1):
            for turn in dialogue:
                f.write(f"{turn}\n")
            if i < num_dialogues:
                f.write("\n")  # Blank line between dialogues
    
    logger.info(f"Created sample raw dialogues file with {num_dialogues} dialogues at {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Annotate dialogues for ontology pipeline evaluation")
    parser.add_argument("--input", help="Path to raw dialogues file")
    parser.add_argument("--output", default="annotated_dialogues.json", help="Path to save annotated dialogues")
    parser.add_argument("--create-sample", action="store_true", help="Create a sample raw dialogues file")
    parser.add_argument("--sample-output", default="sample_raw_dialogues.txt", help="Path to save sample raw dialogues")
    parser.add_argument("--sample-size", type=int, default=2, help="Number of sample dialogues to create")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_raw_dialogues(args.sample_output, args.sample_size)
        return
    
    if not args.input:
        parser.error("--input is required unless using --create-sample")
    
    raw_dialogues = load_raw_dialogues(args.input)
    if not raw_dialogues:
        logger.error(f"No dialogues loaded from {args.input}")
        return
    
    annotated_dialogues = annotate_dialogues_interactive(raw_dialogues)
    save_annotated_dialogues(annotated_dialogues, args.output)

if __name__ == "__main__":
    main() 