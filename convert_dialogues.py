#!/usr/bin/env python3
"""
Dialogue Data Conversion Tool

This script helps convert raw dialogue transcripts into the structured format 
required by the task evaluation metrics system. It provides an interactive interface
to annotate dialogues with task information and error types.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Define task types
TASK_TYPES = [
    "provide_guideline",
    "provide_guideline_detail",
    "provide_guideline_step",
    "provide_specific_handling"
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
            match = re.match(r"(User|Bot):\s*(.*)", line)
            if match:
                speaker, text = match.groups()
                turn = {
                    "id": f"turn_{len(current_dialogue['turns'])+1}",
                    "speaker": speaker.lower(),
                    "text": line,
                    "content": text
                }
                current_dialogue["turns"].append(turn)
        
        # Add the last dialogue if it exists
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
    print("DIALOGUE ANNOTATION TOOL")
    print("="*50)
    print("\nTask types:")
    for i, task_type in enumerate(TASK_TYPES, 1):
        print(f"  {i}. {task_type}")
    
    print("\nError types:")
    for i, error_type in enumerate(ERROR_TYPES, 0):
        print(f"  {i}. {error_type if error_type else 'None'}")
    
    for dialogue in dialogues:
        print("\n" + "="*50)
        print(f"DIALOGUE: {dialogue['id']}")
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
                    "text": turn.get("text", ""),
                    "speaker": "user"
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
                            "text": turn.get("text", ""),
                            "speaker": "bot"
                        })
                        break
                    elif needs_correction in ("y", "yes"):
                        # Get corrected text
                        corrected_text = input("Enter the ideal bot response: ")
                        ground_truth.append({
                            "id": f"gt_{turn['id']}",
                            "text": f"Bot: {corrected_text}",
                            "speaker": "bot"
                        })
                        break
                    print("Please enter 'y' or 'n'")
        
        annotated_dialogue["ground_truth_turns"] = ground_truth
        annotated_dialogues.append(annotated_dialogue)
        
        print("\nDialogue annotation complete!")
    
    return annotated_dialogues

def save_annotated_dialogues(dialogues: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save annotated dialogues to a JSON file
    
    Args:
        dialogues: List of annotated dialogues
        output_file: Path to save the annotations
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dialogues, f, indent=2)
    logger.info(f"Saved {len(dialogues)} annotated dialogues to {output_file}")

def create_sample_raw_dialogues(output_file: str, num_dialogues: int = 3) -> None:
    """
    Create a sample raw dialogues file for testing
    
    Args:
        output_file: Path to save the sample data
        num_dialogues: Number of sample dialogues to create
    """
    dialogues = []
    
    # Sample guideline topics
    topics = ["flood", "earthquake", "disease outbreak", "conflict", "displacement"]
    
    # Sample user questions
    user_questions = [
        "What should I do in case of {topic}?",
        "How can I protect my family during {topic}?",
        "What are the steps to take during {topic}?",
        "Where can I find help during {topic}?",
        "Is there specific advice for {topic} in my area?"
    ]
    
    # Sample bot responses
    bot_responses = [
        "In case of {topic}, you should follow these guidelines: 1. {guideline1} 2. {guideline2} 3. {guideline3}",
        "For {topic} situations, the most important steps are: {guideline1}, {guideline2}, and {guideline3}",
        "I don't have specific information about {topic}. Could you ask a different question?",
        "To protect your family during {topic}, make sure to {guideline1} and {guideline2}",
        "The recommended procedure for {topic} is: First, {guideline1}. Next, {guideline2}. Finally, {guideline3}."
    ]
    
    # Sample guidelines
    guidelines = {
        "flood": ["move to higher ground", "avoid walking through moving water", "listen to emergency broadcasts"],
        "earthquake": ["drop, cover, hold on", "stay away from windows", "check for injuries after shaking stops"],
        "disease outbreak": ["wash hands frequently", "avoid close contact with sick people", "wear a mask in public"],
        "conflict": ["stay away from demonstrations", "keep identity documents secure", "identify evacuation routes"],
        "displacement": ["register with local authorities", "contact humanitarian agencies", "secure clean water sources"]
    }
    
    import random
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for i in range(num_dialogues):
            topic = random.choice(topics)
            
            # Create a dialogue with 2-5 turns
            num_turns = random.randint(2, 5)
            f.write(f"# Dialogue {i+1}\n\n")
            
            for j in range(num_turns):
                if j % 2 == 0:
                    # User turn
                    question = random.choice(user_questions).format(topic=topic)
                    f.write(f"User: {question}\n")
                else:
                    # Bot turn
                    guideline1 = random.choice(guidelines[topic])
                    guideline2 = random.choice([g for g in guidelines[topic] if g != guideline1])
                    guideline3 = random.choice([g for g in guidelines[topic] if g not in [guideline1, guideline2]])
                    
                    response = random.choice(bot_responses).format(
                        topic=topic,
                        guideline1=guideline1,
                        guideline2=guideline2,
                        guideline3=guideline3
                    )
                    f.write(f"Bot: {response}\n")
            
            # Add a blank line between dialogues
            f.write("\n\n")
    
    logger.info(f"Created sample raw dialogues file with {num_dialogues} dialogues at {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert raw dialogues to annotated format")
    
    parser.add_argument("--input", type=str, help="Path to raw dialogues file")
    parser.add_argument("--output", type=str, default="annotated_dialogues.json", 
                       help="Path to save annotated dialogues")
    parser.add_argument("--create-sample", action="store_true", 
                       help="Create sample raw dialogues file")
    parser.add_argument("--sample-output", type=str, default="sample_raw_dialogues.txt",
                       help="Path to save sample raw dialogues")
    parser.add_argument("--num-sample", type=int, default=3,
                       help="Number of sample dialogues to create")
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_raw_dialogues(args.sample_output, args.num_sample)
        sys.exit(0)
    
    if not args.input:
        parser.error("Please provide path to raw dialogues with --input or use --create-sample")
    
    # Load raw dialogues
    dialogues = load_raw_dialogues(args.input)
    
    if not dialogues:
        logger.error("No dialogues loaded. Exiting.")
        sys.exit(1)
    
    # Annotate dialogues
    annotated_dialogues = annotate_dialogues_interactive(dialogues)
    
    # Save annotated dialogues
    save_annotated_dialogues(annotated_dialogues, args.output)
    
    print("\n" + "="*50)
    print("ANNOTATION COMPLETE")
    print("="*50)
    print(f"\nAnnotated {len(annotated_dialogues)} dialogues")
    print(f"Saved to: {args.output}")
    print(f"\nTo evaluate these dialogues, run:")
    print(f"python evaluate_task_metrics.py --dialogues {args.output}")
    print("\n" + "="*50) 