#!/usr/bin/env python3
"""
Simple script to test SPARQL queries against the Fuseki server
"""

import requests
import json

# Configuration
FUSEKI_URL = "http://localhost:3030"
DATASET = "humanitarian"
QUERY_ENDPOINT = f"{FUSEKI_URL}/{DATASET}/query"

# Example queries
QUERIES = {
    "all_camps": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name .
        } LIMIT 10
    """,
    
    "camps_by_manager": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name ?manager WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:managedBy ?managerUri .
            ?managerUri humanitarian:name ?manager .
        } LIMIT 10
    """,
    
    "camps_in_goma": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:hasLocation humanitarian:location_Goma .
        }
    """,
    
    "count_by_status": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?status (COUNT(?camp) as ?count) WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:hasStatus ?status .
        } GROUP BY ?status
    """,
    
    "camps_by_coordinator": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name ?coordinator WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:coordinatedBy ?coordUri .
            ?coordUri humanitarian:name ?coordinator .
        } LIMIT 15
    """,
    
    "large_capacity_camps": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name ?capacity WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:hasCapacity ?capacity .
            FILTER(?capacity > 5000)
        } ORDER BY DESC(?capacity) LIMIT 10
    """,
    
    "camps_by_unhcr": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?camp ?name ?location ?capacity WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:hasLocation ?locUri ;
                  humanitarian:hasCapacity ?capacity ;
                  humanitarian:coordinatedBy humanitarian:organization_UNHCR .
            ?locUri rdfs:label ?location .
        }
    """,
    
    "health_facilities": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?facility ?name ?location WHERE {
            ?facility a humanitarian:HealthFacility ;
                      humanitarian:name ?name ;
                      humanitarian:hasLocation ?locUri .
            ?locUri rdfs:label ?location .
        }
    """,
    
    "camps_managed_by_aides": """
        PREFIX humanitarian: <http://example.org/humanitarian#>
        SELECT ?camp ?name ?status ?capacity WHERE {
            ?camp a humanitarian:Camp ;
                  humanitarian:name ?name ;
                  humanitarian:hasStatus ?status ;
                  humanitarian:hasCapacity ?capacity ;
                  humanitarian:managedBy humanitarian:organization_AIDES .
        } ORDER BY DESC(?capacity) LIMIT 20
    """
}

def run_query(query_name):
    """Run a predefined query and print the results"""
    if query_name not in QUERIES:
        print(f"Query '{query_name}' not found. Available queries: {', '.join(QUERIES.keys())}")
        return
    
    query = QUERIES[query_name]
    
    headers = {
        "Accept": "application/sparql-results+json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "query": query
    }
    
    response = requests.post(QUERY_ENDPOINT, headers=headers, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n=== Results for query: {query_name} ===\n")
        
        # Get the variable names from the response
        variables = result["head"]["vars"]
        
        # Print results in a readable format
        if "results" in result and "bindings" in result["results"]:
            bindings = result["results"]["bindings"]
            if not bindings:
                print("No results found.")
            else:
                # Print header
                header = " | ".join(variables)
                print(header)
                print("-" * len(header))
                
                # Print each row
                for binding in bindings:
                    row = []
                    for var in variables:
                        if var in binding:
                            value = binding[var]["value"]
                            # Clean up URIs to make output more readable
                            if binding[var]["type"] == "uri":
                                value = value.split("/")[-1]
                            row.append(value)
                        else:
                            row.append("")
                    print(" | ".join(row))
                print(f"\nTotal results: {len(bindings)}")
        else:
            print("Unexpected response format:", json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def main():
    """Main function to run the script"""
    print("Available queries:")
    for i, query_name in enumerate(QUERIES.keys(), 1):
        print(f"{i}. {query_name}")
    
    choice = input("\nEnter query number or name (or 'all' to run all queries): ")
    
    if choice.lower() == 'all':
        for query_name in QUERIES:
            run_query(query_name)
    elif choice.isdigit() and 1 <= int(choice) <= len(QUERIES):
        query_name = list(QUERIES.keys())[int(choice) - 1]
        run_query(query_name)
    elif choice in QUERIES:
        run_query(choice)
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main() 