#!/usr/bin/env python3
"""
Excel to RDF Converter for North Kivu Humanitarian Data

This script converts data from the DTM DRC - BA North Kivu Excel file to RDF format
for use in the humanitarian dialogue system.

Usage:
    python excel_to_rdf.py path/to/excel_file.xlsx output_file.ttl

Requirements:
    - pandas
    - rdflib
    - openpyxl
"""

import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD
import argparse
import os
import sys

def create_namespace():
    """Create and return the humanitarian namespace"""
    HUMANITARIAN = Namespace("http://example.org/humanitarian#")
    return HUMANITARIAN

def initialize_graph():
    """Initialize and return RDF graph with appropriate namespaces"""
    g = Graph()
    HUMANITARIAN = create_namespace()
    
    # Bind prefixes for easier reading of the output
    g.bind("humanitarian", HUMANITARIAN)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)
    
    return g, HUMANITARIAN

def load_excel_data(filepath, sheet_name="SITES_CCCM"):
    """Load data from Excel file, specifically from the SITES_CCCM sheet"""
    try:
        print(f"Loading data from {filepath}, sheet: {sheet_name}")
        # Attempt to read the Excel file, focusing on the SITES_CCCM sheet
        try:
            df = pd.read_excel(filepath, sheet_name=sheet_name)
            print(f"Successfully loaded {len(df)} rows of data from {sheet_name} sheet")
            return df
        except ValueError as e:
            # If the specified sheet doesn't exist, list available sheets
            print(f"Error: Sheet '{sheet_name}' not found. Available sheets:")
            xls = pd.ExcelFile(filepath)
            for sheet in xls.sheet_names:
                print(f"  - {sheet}")
            return None
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None

def convert_camp_data(df, graph, ns):
    """
    Convert camp-related data to RDF using French column names
    
    Specifically using the 'NOM DU SITE*' column for camp names
    """
    camp_count = 0
    
    # French column names mapping
    camp_columns = {
        'camp_id': 'CODE SITE*',  # Site code
        'camp_name': 'NOM DU SITE*',  # Site name
        'location': 'TERRITOIRE*',  # Territory
        'capacity': 'MENAGES*',  # Households (fixed: removed accent)
        'status': 'TYPE DE SITE*',  # Site type
        'latitude': 'LATITUDE*',  # Latitude
        'longitude': 'LONGITUDE*',  # Longitude
        'manager': 'GESTIONNAIRE*',  # Site manager
        'coordinator': 'COORDINATEUR*'  # Site coordinator
    }
    
    # Check if any rows exist
    if df.empty:
        print("No data found in the dataframe for camps")
        return graph
    
    # Check if required columns exist
    missing_columns = []
    for column_purpose, column_name in camp_columns.items():
        if column_name not in df.columns:
            missing_columns.append(column_name)
    
    if missing_columns:
        print(f"Warning: The following expected columns are missing: {', '.join(missing_columns)}")
        print("Available columns:", ", ".join(df.columns))
    
    for index, row in df.iterrows():
        # Create a URI for the camp using site code if available, otherwise use index
        if camp_columns['camp_id'] in df.columns and pd.notna(row[camp_columns['camp_id']]):
            camp_id = f"camp_{str(row[camp_columns['camp_id']]).replace(' ', '_')}"
        else:
            camp_id = f"camp_{index}"
        
        camp_uri = URIRef(f"{ns}{camp_id}")
        
        # Add camp type
        graph.add((camp_uri, RDF.type, ns.Camp))
        
        # Add camp name
        if camp_columns['camp_name'] in df.columns and pd.notna(row[camp_columns['camp_name']]):
            camp_name = str(row[camp_columns['camp_name']])
            graph.add((camp_uri, RDFS.label, Literal(camp_name, lang="fr")))
            # Also add as a property
            graph.add((camp_uri, ns.name, Literal(camp_name, lang="fr")))
        
        # Add location/territory
        if camp_columns['location'] in df.columns and pd.notna(row[camp_columns['location']]):
            location_name = str(row[camp_columns['location']])
            location_uri = URIRef(f"{ns}location_{location_name.replace(' ', '_')}")
            
            # Ensure the location exists
            graph.add((location_uri, RDF.type, ns.Location))
            graph.add((location_uri, RDFS.label, Literal(location_name, lang="fr")))
            
            # Link camp to location
            graph.add((camp_uri, ns.hasLocation, location_uri))
        
        # Add capacity (number of households)
        if camp_columns['capacity'] in df.columns and pd.notna(row[camp_columns['capacity']]):
            try:
                capacity = int(row[camp_columns['capacity']])
                graph.add((camp_uri, ns.hasCapacity, Literal(capacity, datatype=XSD.integer)))
            except (ValueError, TypeError):
                # If conversion fails, try to clean the data
                try:
                    capacity_str = str(row[camp_columns['capacity']])
                    # Remove non-numeric characters
                    numeric_str = ''.join(c for c in capacity_str if c.isdigit())
                    if numeric_str:
                        capacity = int(numeric_str)
                        graph.add((camp_uri, ns.hasCapacity, Literal(capacity, datatype=XSD.integer)))
                except:
                    pass
        
        # Add site type/status
        if camp_columns['status'] in df.columns and pd.notna(row[camp_columns['status']]):
            status = str(row[camp_columns['status']])
            graph.add((camp_uri, ns.hasStatus, Literal(status, lang="fr")))
        
        # Add coordinates if available
        if camp_columns['latitude'] in df.columns and pd.notna(row[camp_columns['latitude']]) and \
           camp_columns['longitude'] in df.columns and pd.notna(row[camp_columns['longitude']]):
            try:
                lat = float(row[camp_columns['latitude']])
                lon = float(row[camp_columns['longitude']])
                graph.add((camp_uri, ns.latitude, Literal(lat, datatype=XSD.decimal)))
                graph.add((camp_uri, ns.longitude, Literal(lon, datatype=XSD.decimal)))
            except (ValueError, TypeError):
                pass
        
        # Add manager if available
        if camp_columns['manager'] in df.columns and pd.notna(row[camp_columns['manager']]):
            manager = str(row[camp_columns['manager']])
            graph.add((camp_uri, ns.managedBy, Literal(manager, lang="fr")))
            
            # Also create an NGO entity if needed
            manager_uri = URIRef(f"{ns}organization_{manager.replace(' ', '_')}")
            graph.add((manager_uri, RDF.type, ns.NGO))
            graph.add((manager_uri, RDFS.label, Literal(manager, lang="fr")))
            graph.add((manager_uri, ns.name, Literal(manager, lang="fr")))
            graph.add((camp_uri, ns.managedBy, manager_uri))
        
        # Add coordinator if available
        if camp_columns['coordinator'] in df.columns and pd.notna(row[camp_columns['coordinator']]):
            coordinator = str(row[camp_columns['coordinator']])
            graph.add((camp_uri, ns.coordinatedBy, Literal(coordinator, lang="fr")))
            
            # Also create an NGO entity if needed
            coordinator_uri = URIRef(f"{ns}organization_{coordinator.replace(' ', '_')}")
            graph.add((coordinator_uri, RDF.type, ns.NGO))
            graph.add((coordinator_uri, RDFS.label, Literal(coordinator, lang="fr")))
            graph.add((coordinator_uri, ns.name, Literal(coordinator, lang="fr")))
            graph.add((camp_uri, ns.coordinatedBy, coordinator_uri))
        
        camp_count += 1
    
    print(f"Added {camp_count} camps to the RDF graph")
    return graph

def convert_health_data(df, graph, ns):
    """
    Convert health facility data to RDF
    
    Using the 'ZONE DE SANTE*' column for health facility names
    """
    facility_count = 0
    
    # French column names mapping
    health_columns = {
        'facility_name': 'ZONE DE SANTE*',  # Health zone
        'area': 'AIRE DE SANTE',           # Health area (fixed: removed asterisk)
        'location': 'TERRITOIRE*'           # Territory
    }
    
    # Check if any rows exist
    if df.empty:
        print("No data found in the dataframe for health facilities")
        return graph
    
    # Check if required columns exist
    missing_columns = []
    for column_purpose, column_name in health_columns.items():
        if column_name not in df.columns:
            missing_columns.append(column_name)
    
    if missing_columns:
        print(f"Warning: The following expected health columns are missing: {', '.join(missing_columns)}")
    
    # Process health zones
    health_zones = {}
    if health_columns['facility_name'] in df.columns:
        for index, row in df.iterrows():
            if pd.notna(row[health_columns['facility_name']]):
                health_zone_name = str(row[health_columns['facility_name']])
                
                # Skip if we've already processed this health zone
                if health_zone_name in health_zones:
                    continue
                
                # Create a URI for the health facility
                facility_id = f"health_zone_{health_zone_name.replace(' ', '_')}"
                facility_uri = URIRef(f"{ns}{facility_id}")
                
                # Add type
                graph.add((facility_uri, RDF.type, ns.HealthFacility))
                
                # Add name
                graph.add((facility_uri, RDFS.label, Literal(health_zone_name, lang="fr")))
                graph.add((facility_uri, ns.name, Literal(health_zone_name, lang="fr")))
                
                # Add location if available
                if health_columns['location'] in df.columns and pd.notna(row[health_columns['location']]):
                    location_name = str(row[health_columns['location']])
                    location_uri = URIRef(f"{ns}location_{location_name.replace(' ', '_')}")
                    
                    # Ensure the location exists
                    graph.add((location_uri, RDF.type, ns.Location))
                    graph.add((location_uri, RDFS.label, Literal(location_name, lang="fr")))
                    
                    # Link health facility to location
                    graph.add((facility_uri, ns.hasLocation, location_uri))
                
                # Store this health zone to avoid duplicates
                health_zones[health_zone_name] = facility_uri
                facility_count += 1
    
    # Process health areas
    area_count = 0
    if health_columns['area'] in df.columns:
        for index, row in df.iterrows():
            if pd.notna(row[health_columns['area']]) and pd.notna(row[health_columns['facility_name']]):
                area_name = str(row[health_columns['area']])
                health_zone_name = str(row[health_columns['facility_name']])
                
                # Create a URI for the health area
                area_id = f"health_area_{area_name.replace(' ', '_')}"
                area_uri = URIRef(f"{ns}{area_id}")
                
                # Add type
                graph.add((area_uri, RDF.type, ns.HealthArea))
                
                # Add name
                graph.add((area_uri, RDFS.label, Literal(area_name, lang="fr")))
                graph.add((area_uri, ns.name, Literal(area_name, lang="fr")))
                
                # Link to health zone if it exists
                if health_zone_name in health_zones:
                    zone_uri = health_zones[health_zone_name]
                    graph.add((area_uri, ns.partOf, zone_uri))
                
                area_count += 1
    
    print(f"Added {facility_count} health facilities to the RDF graph")
    print(f"Added {area_count} health areas to the RDF graph")
    return graph

def main():
    parser = argparse.ArgumentParser(description="Convert Excel humanitarian data to RDF")
    parser.add_argument("excel_file", help="Path to the Excel file to convert")
    parser.add_argument("output_file", help="Path to save the output RDF file (in Turtle format)")
    parser.add_argument("--sheet", help="Name of the sheet to process (default: SITES_CCCM)", default="SITES_CCCM")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.excel_file):
        print(f"Error: Input file {args.excel_file} does not exist")
        return
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load data from the specified sheet
    df = load_excel_data(args.excel_file, sheet_name=args.sheet)
    if df is None:
        return
    
    # Initialize RDF graph
    graph, ns = initialize_graph()
    
    # Convert data to RDF
    graph = convert_camp_data(df, graph, ns)
    graph = convert_health_data(df, graph, ns)
    
    # Save to file
    try:
        graph.serialize(destination=args.output_file, format="turtle")
        print(f"Successfully saved RDF data to {args.output_file}")
    except Exception as e:
        print(f"Error saving RDF file: {e}")
        print(f"Exception details: {str(e)}")

if __name__ == "__main__":
    main() 