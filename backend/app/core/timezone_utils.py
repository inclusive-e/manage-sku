"""
Timezone Utilities
Centralized timezone handling for database operations
"""
from datetime import datetime, timezone
from typing import Optional, Union
import pandas as pd


# Default timezone for the application
DEFAULT_TIMEZONE = timezone.utc


def get_utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(DEFAULT_TIMEZONE)


def get_utc_timestamp() -> pd.Timestamp:
    """Get current UTC timestamp for pandas operations"""
    return pd.Timestamp.now(tz="UTC")


def ensure_utc(dt: Optional[Union[datetime, pd.Timestamp]]) -> Optional[datetime]:
    """
    Ensure datetime is UTC timezone-aware
    
    Args:
        dt: datetime or pandas Timestamp (naive or aware)
    
    Returns:
        UTC timezone-aware datetime or None
    """
    if dt is None or pd.isna(dt):
        return None
    
    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is None:
            return dt.tz_localize("UTC").to_pydatetime()
        return dt.tz_convert("UTC").to_pydatetime()
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=DEFAULT_TIMEZONE)
        return dt.astimezone(DEFAULT_TIMEZONE)
    
    return None


def make_naive(dt: Optional[Union[datetime, pd.Timestamp]]) -> Optional[datetime]:
    """
    Convert timezone-aware datetime to naive (remove timezone info)
    Used for columns stored as timestamp without time zone
    
    Args:
        dt: datetime or pandas Timestamp (naive or aware)
    
    Returns:
        Timezone-naive datetime or None
    """
    if dt is None or pd.isna(dt):
        return None
    
    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is not None:
            return dt.tz_localize(None).to_pydatetime()
        return dt.to_pydatetime()
    
    if isinstance(dt, datetime):
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    
    return None


def normalize_pandas_datetime(series: pd.Series) -> pd.Series:
    """
    Normalize pandas datetime series to UTC and make timezone-naive
    Use for date columns stored as timestamp without time zone
    
    Args:
        series: pandas Series with datetime values
    
    Returns:
        Series with timezone-naive UTC datetimes
    """
    if series.dtype != 'datetime64[ns]':
        series = pd.to_datetime(series, errors='coerce')
    
    # If timezone-aware, convert to UTC then remove tz
    if series.dt.tz is not None:
        series = series.dt.tz_convert('UTC').dt.tz_localize(None)
    
    return series
