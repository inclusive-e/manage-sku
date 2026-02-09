"""
Data Processing Service
Reads and processes uploaded files
"""
from typing import Dict, Any, Optional
import pandas as pd
from pathlib import Path

class DataProcessor:
    """Process uploaded data files"""
    
    @staticmethod
    def read_file(file_path: Path) -> pd.DataFrame:
        """Read file based on extension"""
        ext = file_path.suffix.lower()
        
        if ext == '.csv':
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    return pd.read_csv(file_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV file with common encodings")
        
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        
        elif ext == '.txt':
            # Try tab-delimited first, then comma
            try:
                return pd.read_csv(file_path, sep='\t')
            except:
                return pd.read_csv(file_path)
        
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    
    @staticmethod
    def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names"""
        df.columns = df.columns.str.strip()  # Remove whitespace
        df.columns = df.columns.str.lower()  # Lowercase
        df.columns = df.columns.str.replace(' ', '_')  # Spaces to underscores
        df.columns = df.columns.str.replace('-', '_')  # Hyphens to underscores
        df.columns = df.columns.str.replace(r'[^a-z0-9_]', '', regex=True)  # Remove special chars
        return df
    
    @staticmethod
    def infer_and_convert_types(df: pd.DataFrame) -> pd.DataFrame:
        """Infer and convert column types"""
        for col in df.columns:
            # Try numeric first
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                if numeric_data.notna().sum() / len(df) > 0.8:  # 80% numeric
                    df[col] = numeric_data
                    continue
            except:
                pass
            
            # Try datetime
            try:
                date_data = pd.to_datetime(df[col], errors='coerce')
                if date_data.notna().sum() / len(df) > 0.8:  # 80% dates
                    df[col] = date_data
                    continue
            except:
                pass
        
        return df
