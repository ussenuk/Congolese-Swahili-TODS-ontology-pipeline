#!/usr/bin/env python3
"""
Visualization of Ontology Pipeline Evaluation Results

This script creates visualizations for the metrics generated by the evaluation process.
It produces charts for:
1. Task Completion Rate
2. Task Completion Cost
3. Edit Distance

Usage:
    python visualize_results.py --input evaluation_results.json --output metrics_visualization.pdf
"""

import json
import argparse
import logging
import sys
import os
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_evaluation_results(input_file: str) -> dict:
    """
    Load evaluation results from a JSON file
    
    Args:
        input_file: Path to the evaluation results JSON file
    
    Returns:
        Dictionary containing the evaluation metrics
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        logger.info(f"Loaded evaluation results from {input_file}")
        return metrics
    except Exception as e:
        logger.error(f"Failed to load evaluation results from {input_file}: {e}")
        return {}

def create_visualizations(metrics: dict, output_file: str) -> None:
    """
    Create visualizations of the evaluation metrics
    
    Args:
        metrics: Dictionary containing the evaluation metrics
        output_file: Path to save the visualizations
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        # Create a PDF file to save all visualizations
        with PdfPages(output_file) as pdf:
            
            # 1. Task Completion Rate visualization
            if "task_completion_rate" in metrics:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                completion_rates = metrics["task_completion_rate"]
                # Remove 'overall' from bar chart
                if "overall" in completion_rates:
                    overall_rate = completion_rates.pop("overall")
                    task_types = list(completion_rates.keys())
                    rates = list(completion_rates.values())
                else:
                    task_types = list(completion_rates.keys())
                    rates = list(completion_rates.values())
                
                # Create bar chart
                bars = ax.bar(task_types, rates, color='steelblue')
                
                # Add rate values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                            f'{height:.2f}', ha='center', va='bottom')
                
                # Set title and labels
                ax.set_title('Task Completion Rate by Task Type', fontsize=16)
                ax.set_xlabel('Task Type', fontsize=12)
                ax.set_ylabel('Completion Rate', fontsize=12)
                ax.set_ylim(0, 1.1)  # Set y-axis limit to 0-1 with some padding
                
                # Add a horizontal line for overall rate if it exists
                if "overall" in metrics["task_completion_rate"]:
                    ax.axhline(y=overall_rate, color='red', linestyle='--', 
                               label=f'Overall: {overall_rate:.2f}')
                    ax.legend()
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()
            
            # 2. Task Completion Cost visualization
            if "task_completion_cost" in metrics:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                completion_costs = metrics["task_completion_cost"]
                # Remove 'overall' from bar chart
                if "overall" in completion_costs:
                    overall_cost = completion_costs.pop("overall")
                    task_types = list(completion_costs.keys())
                    costs = list(completion_costs.values())
                else:
                    task_types = list(completion_costs.keys())
                    costs = list(completion_costs.values())
                
                # Create bar chart
                bars = ax.bar(task_types, costs, color='lightgreen')
                
                # Add cost values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                            f'{height:.2f}', ha='center', va='bottom')
                
                # Set title and labels
                ax.set_title('Task Completion Cost by Task Type', fontsize=16)
                ax.set_xlabel('Task Type', fontsize=12)
                ax.set_ylabel('Completion Cost (turns)', fontsize=12)
                
                # Add a horizontal line for overall cost if it exists
                if "overall" in metrics["task_completion_cost"]:
                    ax.axhline(y=overall_cost, color='red', linestyle='--', 
                               label=f'Overall: {overall_cost:.2f}')
                    ax.legend()
                
                # Rotate x-axis labels for better readability
                plt.xticks(rotation=45, ha='right')
                
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()
            
            # 3. Edit Distance visualization
            if "edit_distance" in metrics:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                edit_distance = metrics["edit_distance"]
                metrics_names = ["Mean", "Median", "Min", "Max"]
                metrics_values = [
                    edit_distance.get("mean_edit_distance", 0),
                    edit_distance.get("median_edit_distance", 0),
                    edit_distance.get("min_edit_distance", 0),
                    edit_distance.get("max_edit_distance", 0)
                ]
                
                # Create bar chart
                bars = ax.bar(metrics_names, metrics_values, color='salmon')
                
                # Add values on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{height:.2f}', ha='center', va='bottom')
                
                # Set title and labels
                ax.set_title('Edit Distance Metrics', fontsize=16)
                ax.set_xlabel('Metric', fontsize=12)
                ax.set_ylabel('Edit Distance', fontsize=12)
                
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()
            
            # Summary page
            fig, ax = plt.subplots(figsize=(8, 10))
            ax.axis('off')
            
            # Create summary text
            summary_text = "Ontology Pipeline Evaluation Summary\n\n"
            
            if "task_completion_rate" in metrics and "overall" in metrics["task_completion_rate"]:
                summary_text += f"Overall Task Completion Rate: {metrics['task_completion_rate']['overall']:.2f}\n"
            
            if "task_completion_cost" in metrics and "overall" in metrics["task_completion_cost"]:
                summary_text += f"Overall Task Completion Cost: {metrics['task_completion_cost']['overall']:.2f} turns\n"
            
            if "edit_distance" in metrics and "mean_edit_distance" in metrics["edit_distance"]:
                summary_text += f"Mean Edit Distance: {metrics['edit_distance']['mean_edit_distance']:.2f}\n"
            
            summary_text += "\nTask Completion Rate by Type:\n"
            if "task_completion_rate" in metrics:
                for task_type, rate in metrics["task_completion_rate"].items():
                    if task_type != "overall":
                        summary_text += f"  - {task_type}: {rate:.2f}\n"
            
            summary_text += "\nTask Completion Cost by Type:\n"
            if "task_completion_cost" in metrics:
                for task_type, cost in metrics["task_completion_cost"].items():
                    if task_type != "overall":
                        summary_text += f"  - {task_type}: {cost:.2f} turns\n"
            
            # Add summary text to the page
            ax.text(0.1, 0.9, summary_text, transform=ax.transAxes,
                    fontsize=12, verticalalignment='top')
            
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()
        
        logger.info(f"Visualizations saved to {output_file}")
    
    except ImportError:
        logger.error("Matplotlib is required for creating visualizations. Please install it using 'pip install matplotlib'.")
    except Exception as e:
        logger.error(f"Failed to create visualizations: {e}")

def main():
    parser = argparse.ArgumentParser(description="Visualize ontology pipeline evaluation results")
    parser.add_argument("--input", required=True, help="Path to evaluation results JSON file")
    parser.add_argument("--output", default="metrics_visualization.pdf", help="Path to save visualizations PDF")
    
    args = parser.parse_args()
    
    metrics = load_evaluation_results(args.input)
    if metrics:
        create_visualizations(metrics, args.output)

if __name__ == "__main__":
    main() 