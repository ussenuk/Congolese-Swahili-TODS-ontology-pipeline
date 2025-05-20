#!/bin/bash

# Function to check if command succeeded
check_status() {
    if [ $? -ne 0 ]; then
        echo "Error: $1 failed. Exiting."
        exit 1
    fi
}

# Install dependencies only if --install flag is provided
if [ "$1" == "--install" ]; then
    echo "Installing dependencies..."
    echo "Warning: This might modify your current environment."
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install -r requirements.txt
        check_status "Installation"
    else
        echo "Installation skipped."
    fi
fi

# Check for necessary packages without installing
echo "Checking for required packages..."
python -c "import yaml, random, os, sys, numpy, matplotlib" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Warning: Some required packages are missing. Consider running with --install flag."
fi

# Create test data
echo "Creating test data..."
python create_test_data.py
check_status "Test data creation"

# Check if streamlit is installed
if ! python -c "import streamlit" &> /dev/null; then
    echo "Streamlit not found. Would you like to install it?"
    read -p "Install streamlit? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install streamlit==1.27.0
        check_status "Streamlit installation"
    else
        echo "Streamlit installation skipped. Cannot continue without streamlit."
        exit 1
    fi
fi

# Start Streamlit app
echo "Starting Streamlit app for model comparison..."
python -m streamlit run train_evaluate_models.py 