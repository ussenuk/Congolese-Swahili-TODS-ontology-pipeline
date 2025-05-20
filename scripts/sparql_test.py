#!/usr/bin/env python3
"""
SPARQL Test Script

A simple tool to test SPARQL queries against the RDF triple store
for the humanitarian dialogue system.

Usage:
    python sparql_test.py --query <query_file>
    python sparql_test.py --interactive
"""

import argparse
import os
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import json

# Configuration - update this with your SPARQL endpoint
SPARQL_ENDPOINT = "http://localhost:3030/humanitarian/query"

def execute_query(query):
    """Execute a SPARQL query and return the results"""
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    try:
        results = sparql.query().convert()
        return results
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def print_results(results):
    """Format and print query results"""
    if not results or 'results' not in results:
        print("No results or error in query.")
        return
    
    bindings = results['results']['bindings']
    if not bindings:
        print("No matches found.")
        return
    
    # Get column names from the first result
    columns = list(bindings[0].keys())
    
    # Print header
    header = " | ".join(columns)
    separator = "-" * len(header)
    print(separator)
    print(header)
    print(separator)
    
    # Print rows
    for binding in bindings:
        row = []
        for col in columns:
            if col in binding:
                row.append(binding[col]['value'])
            else:
                row.append("")
        print(" | ".join(row))
    
    print(separator)
    print(f"Total results: {len(bindings)}")

def read_query_from_file(file_path):
    """Read a SPARQL query from a file"""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return None
    
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def interactive_mode():
    """Interactive mode for entering SPARQL queries"""
    print("SPARQL Query Interactive Mode")
    print("Enter your SPARQL query (type 'exit' to quit):")
    print("Tip: End your query with a blank line.")
    
    while True:
        print("\nQuery:")
        lines = []
        while True:
            line = input()
            if not line:
                break
            if line.lower() == 'exit':
                return
            lines.append(line)
        
        if not lines:
            continue
        
        query = "\n".join(lines)
        results = execute_query(query)
        
        if results:
            print("\nResults:")
            print_results(results)

def example_queries():
    """Return a dictionary of example SPARQL queries"""
    return {
        "health_facilities": """
PREFIX : <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?facility ?facilityName ?locName
WHERE {
    ?facility rdf:type :HealthFacility .
    ?facility rdfs:label ?facilityName .
    ?facility :hasLocation ?loc .
    ?loc rdfs:label ?locName .
}
""",
        "water_sources": """
PREFIX : <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?source ?sourceName ?locName ?status
WHERE {
    ?source rdf:type :WaterSource .
    ?source rdfs:label ?sourceName .
    ?source :hasLocation ?loc .
    ?loc rdfs:label ?locName .
    ?source :hasStatus ?status .
}
""",
        "camps": """
PREFIX : <http://example.org/humanitarian#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?camp ?campName ?locName ?capacity ?status
WHERE {
    ?camp rdf:type :Camp .
    ?camp rdfs:label ?campName .
    ?camp :hasLocation ?loc .
    ?loc rdfs:label ?locName .
    ?camp :hasCapacity ?capacity .
    ?camp :hasStatus ?status .
}
"""
    }

def show_examples():
    """Show example queries"""
    examples = example_queries()
    
    print("Available example queries:")
    for i, name in enumerate(examples.keys(), 1):
        print(f"{i}. {name}")
    
    while True:
        choice = input("\nEnter example number (or 'q' to quit): ")
        if choice.lower() == 'q':
            return
        
        try:
            index = int(choice) - 1
            keys = list(examples.keys())
            if 0 <= index < len(keys):
                selected = keys[index]
                print(f"\n--- {selected} ---")
                print(examples[selected])
                
                execute = input("\nExecute this query? (y/n): ")
                if execute.lower() == 'y':
                    results = execute_query(examples[selected])
                    if results:
                        print("\nResults:")
                        print_results(results)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def main():
    parser = argparse.ArgumentParser(description="SPARQL query testing tool")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--query", help="Path to file containing SPARQL query")
    group.add_argument("--interactive", action="store_true", help="Start interactive mode")
    group.add_argument("--examples", action="store_true", help="Show example queries")
    
    args = parser.parse_args()
    
    if args.query:
        query = read_query_from_file(args.query)
        if query:
            print(f"Executing query from {args.query}:")
            results = execute_query(query)
            if results:
                print_results(results)
    elif args.interactive:
        interactive_mode()
    elif args.examples:
        show_examples()
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 