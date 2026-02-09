# Phase 2: Data Processing Pipeline - Technical Plan

## Overview

**Status**: 🔄 IN PROGRESS  
**Goal**: Clean, validate, and prepare uploaded sales data for analysis and model training  
**Duration**: 1-2 weeks  
**Priority**: HIGH (blocks all ML work)

---

## Current State

**What's Working**:
- ✅ File upload with validation
- ✅ Schema detection (date, numeric, categorical)
- ✅ Basic data preview
- ✅ Missing value handling (defaults filled)
- ✅ Database storage for upload metadata

**What's Missing**:
- ❌ Data cleaning (anomaly handling)
- ❌ Duplicate detection
- ❌ Outlier flagging
- ❌ Data transformations
- ❌ Cleaned data persistence to `sales_data` table

---

## Technical Architecture

### Data Flow

```
RawUpload (metadata)
      ↓
Read File → Clean Columns → Infer Types → Fill Missing → Detect Anomalies
      ↓                                                    ↓
Cleaned DataFrame                                  Validation Report
      ↓                                                    ↓
Transform Data                                      User Review
      ↓                                                    ↓
Save to sales_data table                           Approve/Reject
```

### Database Schema

```sql
-- Raw upload metadata (exists)
CREATE TABLE raw_uploads (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    row_count INTEGER,
    column_count INTEGER,
    detected_schema JSONB,
    validation_report JSONB,
    column_mapping JSONB,
    status VARCHAR(50), -- 'uploaded', 'processing', 'processed', 'error'
    error_message TEXT,
    uploaded_at TIMESTAMP,
    processed_at TIMESTAMP
);

-- Cleaned sales data (to be populated)
CREATE TABLE sales_data (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(36) REFERENCES raw_uploads(id),
    
    -- Core fields (required)
    date DATE NOT NULL,
    sku_id VARCHAR(100) NOT NULL,
    
    -- Sales metrics
    sales_quantity DECIMAL(10,2),
    unit_price DECIMAL(10,2),
    sales_revenue DECIMAL(12,2),
    
    -- Inventory
    stock_level INTEGER,
    
    -- SKU attributes
    category VARCHAR(100),
    
    -- Data quality flags
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_flags JSONB, -- ['future_date', 'negative_quantity', 'outlier']
    
    -- Audit trail
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_sales_data_upload ON sales_data(upload_id);
CREATE INDEX idx_sales_data_sku_date ON sales_data(sku_id, date);
CREATE INDEX idx_sales_data_date ON sales_data(date);
CREATE INDEX idx_sales_data_anomaly ON sales_data(is_anomaly) WHERE is_anomaly = TRUE;
```

---

## Component Breakdown

### 1. Data Cleaning Service

**File**: `backend/app/services/data_cleaner.py`

**Responsibilities**:
- Detect and handle anomalies
- Remove/fix duplicates
- Standardize formats
- Flag suspicious data

**Implementation**:

```python
class DataCleaner:
    """Clean and standardize sales data"""
    
    @staticmethod
    def detect_anomalies(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
        """
        Detect anomalies and add flags
        
        Returns DataFrame with additional columns:
        - is_anomaly: bool
        - anomaly_flags: list of strings
        """
        pass
    
    @staticmethod
    def handle_duplicates(df: pd.DataFrame, keep: str = 'first') -> pd.DataFrame:
        """
        Detect and remove duplicate rows
        
        Args:
            keep: 'first', 'last', or False (remove all)
        """
        pass
    
    @staticmethod
    def standardize_formats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize data formats:
        - Date formats to ISO
        - Currency to decimal
        - SKUs to uppercase
        """
        pass
    
    @staticmethod
    def calculate_outliers(df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.Series:
        """
        Calculate outlier flags using IQR or Z-score
        
        Returns boolean series indicating outliers
        """
        pass
```

**Anomaly Types to Detect**:

1. **Temporal Anomalies**
   - Future dates (after today)
   - Very old dates (before 2000)
   - Invalid date formats
   - Weekends/holidays (flag, don't remove)

2. **Quantity Anomalies**
   - Negative values (returns - valid but flag)
   - Zero values (flag if unexpected)
   - Extreme outliers (>3 std dev or outside IQR)
   - Decimal quantities (for discrete items)

3. **Price Anomalies**
   - Negative prices
   - Zero prices
   - Price changes >50% from median
   - Extreme outliers

4. **SKU Anomalies**
   - Invalid SKU formats
   - New SKUs not in historical data
   - Duplicate SKUs with different categories

---

### 2. Data Transformation Service

**File**: `backend/app/services/data_transformer.py`

**Responsibilities**:
- Currency normalization
- Unit conversions
- Categorical encoding
- Feature engineering (basic)

**Implementation**:

```python
class DataTransformer:
    """Transform data for analysis"""
    
    @staticmethod
    def normalize_currency(df: pd.DataFrame, column: str, target_currency: str = 'USD') -> pd.DataFrame:
        """Convert all currencies to target currency"""
        pass
    
    @staticmethod
    def encode_categories(df: pd.DataFrame, column: str, method: str = 'onehot') -> pd.DataFrame:
        """
        Encode categorical variables
        
        Methods: 'onehot', 'label', 'target'
        """
        pass
    
    @staticmethod
    def aggregate_by_period(df: pd.DataFrame, period: str = 'D') -> pd.DataFrame:
        """
        Aggregate data by time period
        
        period: 'D' (daily), 'W' (weekly), 'M' (monthly)
        """
        pass
    
    @staticmethod
    def calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived fields:
        - revenue = quantity * price
        - discount_pct
        - profit_margin (if cost available)
        """
        pass
```

---

### 3. Processing Pipeline Orchestrator

**File**: `backend/app/services/processing_pipeline.py`

**Responsibilities**:
- Orchestrate the full processing flow
- Handle errors and rollback
- Update status in database
- Generate processing report

**Implementation**:

```python
class ProcessingPipeline:
    """Orchestrate data processing workflow"""
    
    def __init__(self, upload_id: str):
        self.upload_id = upload_id
        self.steps_completed = []
        self.errors = []
        self.stats = {}
    
    async def process(self) -> dict:
        """
        Execute full processing pipeline
        
        Returns processing report with:
        - rows_processed
        - rows_anomalous
        - duplicates_removed
        - errors
        """
        try:
            # 1. Load raw data
            df = await self._load_raw_data()
            
            # 2. Clean data
            df = self._clean_data(df)
            
            # 3. Transform data
            df = self._transform_data(df)
            
            # 4. Validate cleaned data
            validation = self._validate_cleaned(df)
            
            # 5. Save to sales_data
            await self._save_cleaned_data(df)
            
            # 6. Update upload status
            await self._update_status('processed')
            
            return self._generate_report()
            
        except Exception as e:
            await self._update_status('error', str(e))
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning steps"""
        from app.services.data_cleaner import DataCleaner
        
        # Detect anomalies
        df = DataCleaner.detect_anomalies(df, self.schema)
        
        # Handle duplicates
        df = DataCleaner.handle_duplicates(df)
        
        # Standardize formats
        df = DataCleaner.standardize_formats(df)
        
        return df
```

---

## API Endpoints

### 1. Process Upload

```python
@router.post("/uploads/{upload_id}/process")
async def process_upload(
    upload_id: str,
    options: ProcessingOptions = Body(default=ProcessingOptions())
):
    """
    Process uploaded file and save to sales_data table
    
    Body:
    {
        "remove_duplicates": true,
        "remove_outliers": false,
        "outlier_method": "iqr",
        "currency": "USD"
    }
    
    Returns:
    {
        "upload_id": "uuid",
        "status": "processed",
        "rows_processed": 500,
        "rows_anomalous": 25,
        "duplicates_removed": 5,
        "processing_time_seconds": 3.2,
        "report": {...}
    }
    """
    pass
```

### 2. Get Processing Status

```python
@router.get("/uploads/{upload_id}/processing-status")
async def get_processing_status(upload_id: str):
    """
    Get detailed processing status and report
    """
    pass
```

### 3. Preview Cleaned Data

```python
@router.get("/uploads/{upload_id}/preview-cleaned")
async def preview_cleaned_data(
    upload_id: str,
    page: int = 1,
    page_size: int = 50
):
    """
    Preview cleaned data before final save
    """
    pass
```

### 4. Get Anomalies

```python
@router.get("/uploads/{upload_id}/anomalies")
async def get_anomalies(upload_id: str, flag_type: Optional[str] = None):
    """
    Get list of anomalous rows
    
    Query params:
    - flag_type: 'future_date', 'negative_quantity', 'outlier', 'duplicate'
    """
    pass
```

---

## Frontend Components

### 1. Processing Review Page

**File**: `frontend/src/pages/DataReview.tsx`

**Features**:
- Side-by-side comparison (raw vs cleaned)
- Anomaly highlighting
- Approve/Reject individual rows
- Bulk actions (remove all outliers, etc.)
- Processing statistics dashboard

### 2. Anomaly Viewer

**File**: `frontend/src/components/AnomalyViewer.tsx`

**Features**:
- Filter by anomaly type
- Color-coded rows
- Quick actions (ignore, fix, remove)
- Export anomaly report

### 3. Processing Status Monitor

**File**: `frontend/src/components/ProcessingStatus.tsx`

**Features**:
- Real-time progress bar
- Step-by-step status
- Error display
- Cancel/Retry buttons

---

## Processing Options Configuration

```typescript
interface ProcessingOptions {
  // Duplicate handling
  removeDuplicates: boolean;
  duplicateKeepStrategy: 'first' | 'last' | 'none';
  
  // Outlier handling
  detectOutliers: boolean;
  outlierMethod: 'iqr' | 'zscore';
  outlierThreshold: number; // 1.5 for IQR, 3 for Z-score
  removeOutliers: boolean; // or just flag them
  
  // Anomaly handling
  flagFutureDates: boolean;
  flagNegativeQuantities: boolean; // for returns
  flagZeroQuantities: boolean;
  
  // Transformations
  normalizeCurrency: boolean;
  targetCurrency: string;
  aggregateBy: 'day' | 'week' | 'month';
  
  // Data quality
  requireAllFields: boolean;
  minDate: string;
  maxDate: string;
}
```

---

## Error Handling Strategy

### Levels

1. **Row-level errors** (skip row, log warning)
   - Invalid date format
   - Non-numeric in numeric column
   - Missing required field

2. **Column-level errors** (skip column, use defaults)
   - All values null
   - Inconsistent types
   - Encoding issues

3. **File-level errors** (fail processing)
   - Empty file
   - All rows invalid
   - Schema mismatch
   - Database connection failure

### Error Response Format

```json
{
  "status": "partial_success",
  "upload_id": "uuid",
  "rows_processed": 495,
  "rows_failed": 5,
  "errors": [
    {
      "row": 45,
      "column": "date",
      "error": "Invalid date format: '2024-13-45'",
      "severity": "warning",
      "action": "skipped"
    }
  ],
  "summary": "5 rows skipped due to validation errors"
}
```

---

## Performance Considerations

### For Large Files (>100k rows)

1. **Chunked Processing**
   - Process in batches of 10k rows
   - Use generators to minimize memory
   - Streaming inserts to database

2. **Background Processing**
   - Move processing to Celery/RQ worker
   - Return job ID immediately
   - Poll for status updates
   - WebSocket notifications on completion

3. **Database Optimization**
   - Batch inserts (1000 rows at a time)
   - Use COPY command for bulk load
   - Disable indexes during insert, re-enable after
   - Transaction per chunk

### Estimated Processing Times

| File Size | Rows | Processing Time |
|-----------|------|-----------------|
| Small | < 10k | < 5 seconds |
| Medium | 10k-100k | 10-30 seconds |
| Large | 100k-1M | 1-5 minutes |
| Very Large | > 1M | 5-15 minutes (background) |

---

## Testing Strategy

### Unit Tests

```python
# Test data cleaner
def test_detect_future_dates():
    df = pd.DataFrame({'date': ['2024-01-01', '2025-12-01']})
    result = DataCleaner.detect_anomalies(df, {})
    assert result['is_anomaly'].iloc[1] == True

def test_handle_duplicates():
    df = pd.DataFrame({'sku': ['A', 'A', 'B'], 'qty': [1, 1, 2]})
    result = DataCleaner.handle_duplicates(df)
    assert len(result) == 2

def test_calculate_outliers_iqr():
    data = [1, 2, 3, 4, 100]  # 100 is outlier
    result = DataCleaner.calculate_outliers(pd.Series(data), 'iqr')
    assert result.iloc[4] == True
```

### Integration Tests

```python
async def test_full_processing_pipeline():
    # Upload test file
    upload_id = await upload_test_file('sample_with_anomalies.csv')
    
    # Process
    result = await process_upload(upload_id)
    
    # Verify
    assert result['rows_processed'] == 500
    assert result['rows_anomalous'] == 85
    assert result['duplicates_removed'] == 5
    
    # Check database
    rows = await db.query(f"SELECT * FROM sales_data WHERE upload_id = '{upload_id}'")
    assert len(rows) == 495  # 500 - 5 duplicates
```

---

## Implementation Checklist

### Week 1: Core Cleaning

- [ ] Create `data_cleaner.py` with anomaly detection
- [ ] Implement duplicate detection
- [ ] Add outlier calculation (IQR, Z-score)
- [ ] Create `data_transformer.py` with basic transforms
- [ ] Write unit tests for all cleaning functions
- [ ] Create database migration for `sales_data` table

### Week 2: Pipeline & API

- [ ] Create `processing_pipeline.py` orchestrator
- [ ] Implement `/process` endpoint
- [ ] Add processing status tracking
- [ ] Create frontend processing review page
- [ ] Add anomaly viewer component
- [ ] Write integration tests
- [ ] Performance testing with large files
- [ ] Error handling and edge cases

### Week 3: Polish & Optimization

- [ ] Add background processing for large files
- [ ] Implement chunked processing
- [ ] Add progress tracking with WebSockets
- [ ] Create processing analytics dashboard
- [ ] Documentation and examples
- [ ] End-to-end testing

---

## Dependencies to Add

```txt
# Already have
pandas>=2.2.0
numpy>=2.1.0

# For background processing (Week 3)
celery>=5.3.0
redis>=5.0.0

# For advanced outlier detection
scipy>=1.11.0

# For currency conversion (optional)
forex-python>=1.8
```

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large files cause memory issues | High | Implement chunked processing, streaming |
| Database timeout on bulk insert | Medium | Batch inserts, use COPY command |
| Processing takes too long | Medium | Background jobs, progress tracking |
| Data loss during cleaning | High | Preview before save, soft deletes |
| Anomaly detection too aggressive | Low | Configurable thresholds, user review |

---

## Success Criteria

✅ **Phase 2 Complete When**:
1. Can process sample_sales_data.csv without errors
2. All 85 anomalies detected and flagged correctly
3. 5 duplicates removed
4. Cleaned data saved to sales_data table
5. Processing completes in < 10 seconds for 500 rows
6. Frontend shows preview with anomalies highlighted
7. User can approve/reject before final save
8. All tests passing (unit + integration)

---

## Next Steps

1. **Start with data_cleaner.py** - Implement anomaly detection
2. **Create database migration** - Add sales_data table
3. **Build processing endpoint** - Wire up the pipeline
4. **Create frontend review page** - Allow user approval
5. **Test with sample data** - Verify all anomalies caught

**Blocked by**: Nothing! Can start immediately.

**Blocks**: Phase 3 (Feature Engineering) - needs clean data
