"""Data processing pipeline"""

import pandas as pd
from pathlib import Path
import argparse


def load_data(input_path: str) -> pd.DataFrame:
    """Load data from CSV file"""
    return pd.read_csv(input_path)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate data"""
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Fill missing values
    df = df.fillna(0)
    
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform data"""
    # Add computed columns
    if 'value' in df.columns:
        df['value_squared'] = df['value'] ** 2
        df['value_log'] = df['value'].apply(lambda x: x if x > 0 else 0)
    
    return df


def export_data(df: pd.DataFrame, output_path: str) -> None:
    """Export data to CSV"""
    df.to_csv(output_path, index=False)


def main():
    """Main pipeline execution"""
    parser = argparse.ArgumentParser(description='Data processing pipeline')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    args = parser.parse_args()
    
    # Execute pipeline
    print("Loading data...")
    df = load_data(args.input)
    
    print("Cleaning data...")
    df = clean_data(df)
    
    print("Transforming data...")
    df = transform_data(df)
    
    print("Exporting data...")
    export_data(df, args.output)
    
    print("Pipeline completed successfully!")


if __name__ == '__main__':
    main()
