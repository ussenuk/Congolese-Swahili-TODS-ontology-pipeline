"""
Text Extraction and Preprocessing for Humanitarian Data

This module provides functions to extract and preprocess text from 
HDX datasets (Excel files) for input into the entity recognition model.
"""

import pandas as pd
import re
import nltk
from nltk.tokenize import sent_tokenize
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download necessary NLTK resources if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def load_hdx_data(excel_file_path, sheet_name=None):
    """
    Load data from an HDX Excel file
    
    Args:
        excel_file_path: Path to the Excel file
        sheet_name: Name of the sheet to load (if None, loads all sheets)
        
    Returns:
        DataFrame with the loaded data
    """
    try:
        if sheet_name:
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
            logger.info(f"Loaded {len(df)} rows from sheet '{sheet_name}'")
        else:
            # List all available sheets and load them
            xls = pd.ExcelFile(excel_file_path)
            sheet_names = xls.sheet_names
            
            # Load the first sheet by default or create empty DataFrame
            if sheet_names:
                df = pd.read_excel(excel_file_path, sheet_name=sheet_names[0])
                logger.info(f"Loaded {len(df)} rows from sheet '{sheet_names[0]}'")
            else:
                df = pd.DataFrame()
                logger.warning("No sheets found in the Excel file")
        
        return df
    except Exception as e:
        logger.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

def clean_text(text):
    """
    Clean text by removing extra whitespace, expanding units, and normalizing punctuation
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Expand units (e.g., "5km" to "5 kilometers")
    text = re.sub(r'(\d+)km', r'\1 kilometers', text)
    text = re.sub(r'(\d+)m', r'\1 meters', text)
    text = re.sub(r'(\d+)l', r'\1 liters', text)
    
    # Normalize punctuation
    text = re.sub(r'[^\w\s.,?!;:]', ' ', text)
    
    # Remove tab characters
    text = text.replace('\t', ' ')
    
    return text.strip()

def extract_humanitarian_text(df, text_columns=None):
    """
    Extract humanitarian-related text from specific columns in a DataFrame
    
    Args:
        df: DataFrame containing the HDX data
        text_columns: List of column names to extract text from (if None, uses all string columns)
        
    Returns:
        List of extracted and cleaned text segments
    """
    if df.empty:
        logger.warning("Empty DataFrame provided")
        return []
    
    # If no columns specified, use all object/string columns
    if not text_columns:
        text_columns = df.select_dtypes(include=['object']).columns.tolist()
        logger.info(f"Using all string columns: {text_columns}")
    
    # Extract text from specified columns
    texts = []
    
    for column in text_columns:
        if column in df.columns:
            # Extract non-null values from the column
            column_texts = df[column].dropna().astype(str).tolist()
            
            # Clean each text segment
            cleaned_texts = [clean_text(text) for text in column_texts]
            
            # Filter out empty strings
            cleaned_texts = [text for text in cleaned_texts if text]
            
            texts.extend(cleaned_texts)
            logger.info(f"Extracted {len(cleaned_texts)} text segments from column '{column}'")
        else:
            logger.warning(f"Column '{column}' not found in DataFrame")
    
    return texts

def tokenize_sentences(texts):
    """
    Tokenize a list of text segments into sentences
    
    Args:
        texts: List of text segments
        
    Returns:
        List of sentences
    """
    sentences = []
    
    for text in texts:
        # Tokenize into sentences
        text_sentences = sent_tokenize(text)
        sentences.extend(text_sentences)
    
    logger.info(f"Tokenized into {len(sentences)} sentences")
    return sentences

def extract_and_preprocess_hdx_data(excel_file_path, sheet_name=None, text_columns=None):
    """
    Extract and preprocess text from an HDX Excel file
    
    Args:
        excel_file_path: Path to the Excel file
        sheet_name: Name of the sheet to load (if None, loads all sheets)
        text_columns: List of column names to extract text from
        
    Returns:
        List of preprocessed sentences for entity recognition
    """
    # Load the data
    df = load_hdx_data(excel_file_path, sheet_name)
    
    if df.empty:
        logger.warning("No data loaded from Excel file")
        return []
    
    # Extract text from the DataFrame
    texts = extract_humanitarian_text(df, text_columns)
    
    if not texts:
        logger.warning("No text extracted from DataFrame")
        return []
    
    # Tokenize into sentences
    sentences = tokenize_sentences(texts)
    
    return sentences

def extract_humanitarian_concepts(sentences):
    """
    Extract humanitarian concepts from sentences
    This is a placeholder for more sophisticated extraction methods
    
    Args:
        sentences: List of sentences
        
    Returns:
        List of humanitarian concepts
    """
    # This is a simple rule-based approach that could be replaced with a more sophisticated model
    humanitarian_keywords = [
        "camp", "refugee", "displaced", "health", "water", "food", "security",
        "shelter", "education", "protection", "assistance", "aid", "distribution",
        "facility", "service", "medicine", "disease", "nutrition", "hygiene",
        "kambi", "wakimbizi", "afya", "maji", "chakula", "usalama", "msaada"
    ]
    
    concepts = []
    
    for sentence in sentences:
        words = sentence.lower().split()
        for keyword in humanitarian_keywords:
            if keyword in words:
                # Extract the context around the keyword
                start_idx = max(0, words.index(keyword) - 2)
                end_idx = min(len(words), words.index(keyword) + 3)
                concept = " ".join(words[start_idx:end_idx])
                concepts.append(concept)
                break
    
    logger.info(f"Extracted {len(concepts)} humanitarian concepts")
    return concepts

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python preprocessing.py <excel_file_path> [sheet_name]")
        sys.exit(1)
    
    excel_file_path = sys.argv[1]
    sheet_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    sentences = extract_and_preprocess_hdx_data(excel_file_path, sheet_name)
    
    print(f"Extracted {len(sentences)} sentences")
    if sentences:
        print("Sample sentences:")
        for i, sentence in enumerate(sentences[:5]):
            print(f"{i+1}. {sentence}")
        
        concepts = extract_humanitarian_concepts(sentences)
        print(f"\nExtracted {len(concepts)} humanitarian concepts")
        if concepts:
            print("Sample concepts:")
            for i, concept in enumerate(concepts[:5]):
                print(f"{i+1}. {concept}") 