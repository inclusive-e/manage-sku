"""
Data Validation Service
Validates data quality and reports issues
"""
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
from enum import Enum

class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Must fix
    WARNING = "warning"  # Should fix
    INFO = "info"        # Good to know

class DataValidator:
    """Validates data quality and structure"""
    
    # Required columns for sales data
    REQUIRED_COLUMN_MAPPINGS = ['date', 'sku', 'quantity']  # At minimum
    
    @staticmethod
    def validate_file_structure(df: pd.DataFrame) -> List[Dict]:
        """Validate basic file structure"""
        issues = []
        
        # Check if empty
        if len(df) == 0:
            issues.append({
                'severity': ValidationSeverity.ERROR.value,
                'type': 'empty_file',
                'message': 'File contains no data rows',
                'suggestion': 'Upload a file with at least one data row'
            })
        
        # Check if too many columns
        if len(df.columns) > 50:
            issues.append({
                'severity': ValidationSeverity.WARNING.value,
                'type': 'too_many_columns',
                'message': f'File has {len(df.columns)} columns, which is unusual',
                'suggestion': 'Ensure the first row contains column headers'
            })
        
        # Check if too few columns
        if len(df.columns) < 2:
            issues.append({
                'severity': ValidationSeverity.ERROR.value,
                'type': 'too_few_columns',
                'message': 'File has less than 2 columns',
                'suggestion': 'Sales data typically has date, SKU, and quantity columns'
            })
        
        return issues
    
    @staticmethod
    def validate_missing_values(df: pd.DataFrame, schema: Dict) -> List[Dict]:
        """Check for missing values in critical columns"""
        issues = []
        
        for col_info in schema['columns']:
            null_pct = col_info['null_percentage']
            col_name = col_info['name']
            
            if null_pct > 50:
                issues.append({
                    'severity': ValidationSeverity.ERROR.value,
                    'type': 'excessive_missing_values',
                    'column': col_name,
                    'message': f'Column "{col_name}" has {null_pct:.1f}% missing values',
                    'suggestion': 'This column may not be useful for analysis'
                })
            elif null_pct > 20:
                issues.append({
                    'severity': ValidationSeverity.WARNING.value,
                    'type': 'high_missing_values',
                    'column': col_name,
                    'message': f'Column "{col_name}" has {null_pct:.1f}% missing values',
                    'suggestion': 'Consider filling missing values or removing this column'
                })
            elif null_pct > 0:
                issues.append({
                    'severity': ValidationSeverity.INFO.value,
                    'type': 'missing_values',
                    'column': col_name,
                    'message': f'Column "{col_name}" has {null_pct:.1f}% missing values',
                    'suggestion': 'Missing values will be handled during processing'
                })
        
        return issues
    
    @staticmethod
    def validate_date_range(df: pd.DataFrame, date_column: str) -> List[Dict]:
        """Validate date column has reasonable range"""
        issues = []
        
        if date_column not in df.columns:
            return issues
        
        try:
            dates = pd.to_datetime(df[date_column], errors='coerce')
            valid_dates = dates.dropna()
            
            if len(valid_dates) == 0:
                issues.append({
                    'severity': ValidationSeverity.ERROR.value,
                    'type': 'invalid_dates',
                    'column': date_column,
                    'message': f'Could not parse dates in column "{date_column}"',
                    'suggestion': 'Ensure dates are in YYYY-MM-DD format'
                })
                return issues
            
            min_date = valid_dates.min()
            max_date = valid_dates.max()
            now = pd.Timestamp.now()
            
            # Check for future dates
            if max_date > now:
                future_count = (dates > now).sum()
                issues.append({
                    'severity': ValidationSeverity.WARNING.value,
                    'type': 'future_dates',
                    'column': date_column,
                    'message': f'{future_count} rows have future dates',
                    'suggestion': 'Future dates may indicate data entry errors'
                })
            
            # Check for very old dates
            if min_date < pd.Timestamp('2000-01-01'):
                old_count = (dates < pd.Timestamp('2000-01-01')).sum()
                issues.append({
                    'severity': ValidationSeverity.WARNING.value,
                    'type': 'very_old_dates',
                    'column': date_column,
                    'message': f'{old_count} rows have dates before year 2000',
                    'suggestion': 'Old dates may indicate incorrect data'
                })
            
            # Check date range
            date_range_days = (max_date - min_date).days
            if date_range_days < 30:
                issues.append({
                    'severity': ValidationSeverity.WARNING.value,
                    'type': 'short_date_range',
                    'column': date_column,
                    'message': f'Data spans only {date_range_days} days',
                    'suggestion': 'Forecasting works best with at least 3 months of data'
                })
            
        except Exception as e:
            issues.append({
                'severity': ValidationSeverity.ERROR.value,
                'type': 'date_validation_error',
                'column': date_column,
                'message': f'Error validating dates: {str(e)}',
                'suggestion': 'Check date format'
            })
        
        return issues
    
    @staticmethod
    def validate_numeric_values(df: pd.DataFrame, numeric_columns: List[str]) -> List[Dict]:
        """Validate numeric columns for outliers and negative values"""
        issues = []
        
        for col in numeric_columns:
            if col not in df.columns:
                continue
            
            try:
                numeric_data = pd.to_numeric(df[col], errors='coerce')
                
                # Check for negative values
                negative_count = (numeric_data < 0).sum()
                if negative_count > 0:
                    issues.append({
                        'severity': ValidationSeverity.INFO.value,
                        'type': 'negative_values',
                        'column': col,
                        'message': f'{negative_count} rows have negative values in "{col}"',
                        'suggestion': 'Negative values may be valid for returns/discounts'
                    })
                
                # Check for zeros
                zero_count = (numeric_data == 0).sum()
                if zero_count > len(df) * 0.5:
                    issues.append({
                        'severity': ValidationSeverity.WARNING.value,
                        'type': 'many_zeros',
                        'column': col,
                        'message': f'More than 50% of values in "{col}" are zero',
                        'suggestion': 'Many zeros may indicate missing data coded as zero'
                    })
                
            except:
                pass
        
        return issues
    
    @staticmethod
    def validate_data(df: pd.DataFrame, schema: Dict) -> Dict[str, Any]:
        """
        Run all validations and return comprehensive report
        
        Returns:
            {
                'is_valid': True/False,
                'total_issues': 5,
                'errors': 1,
                'warnings': 3,
                'infos': 1,
                'issues': [...],
                'summary': 'File has 1 error that must be fixed'
            }
        """
        all_issues = []
        
        # Run all validations
        all_issues.extend(DataValidator.validate_file_structure(df))
        all_issues.extend(DataValidator.validate_missing_values(df, schema))
        
        # Validate date column if detected
        date_col = schema.get('suggested_date_column')
        if date_col:
            all_issues.extend(DataValidator.validate_date_range(df, date_col))
        
        # Validate numeric columns
        numeric_cols = [c['name'] for c in schema['columns'] if c['detected_type'] in ['numeric', 'integer']]
        all_issues.extend(DataValidator.validate_numeric_values(df, numeric_cols))
        
        # Count by severity
        errors = [i for i in all_issues if i['severity'] == ValidationSeverity.ERROR.value]
        warnings = [i for i in all_issues if i['severity'] == ValidationSeverity.WARNING.value]
        infos = [i for i in all_issues if i['severity'] == ValidationSeverity.INFO.value]
        
        # Determine if valid (no errors)
        is_valid = len(errors) == 0
        
        # Generate summary
        if len(errors) > 0:
            summary = f"File has {len(errors)} error(s) that must be fixed before processing"
        elif len(warnings) > 0:
            summary = f"File is valid but has {len(warnings)} warning(s)"
        else:
            summary = "File validation passed with no issues"
        
        return {
            'is_valid': is_valid,
            'total_issues': len(all_issues),
            'errors': len(errors),
            'warnings': len(warnings),
            'infos': len(infos),
            'issues': all_issues,
            'summary': summary
        }
