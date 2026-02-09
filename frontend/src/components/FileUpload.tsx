import { useState, useCallback } from 'react';
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface UploadResponse {
  upload_id: string;
  filename: string;
  status: string;
  row_count: number;
  column_count: number;
  schema: {
    columns: Array<{
      name: string;
      detected_type: string;
      suggested_mapping: string | null;
      null_count: number;
      null_percentage: number;
      unique_count: number;
      sample_values: string[];
    }>;
    row_count: number;
    column_count: number;
    suggested_date_column: string | null;
    suggested_sku_column: string | null;
    memory_usage_mb: number;
  };
  validation: {
    is_valid: boolean;
    total_issues: number;
    errors: number;
    warnings: number;
    infos: number;
    issues: Array<{
      severity: string;
      type: string;
      column?: string;
      message: string;
      suggestion: string;
    }>;
    summary: string;
  };
  preview: Array<Record<string, string | number | null>>;
}

export function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  }, []);

  const validateAndSetFile = (file: File) => {
    const allowedTypes = ['.csv', '.xlsx', '.xls', '.txt'];
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(ext)) {
      setError(`Invalid file type. Allowed: ${allowedTypes.join(', ')}`);
      return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
      setError('File too large. Maximum size: 50MB');
      return;
    }
    
    setFile(file);
    setError(null);
    setUploadResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch(`${API_URL}/api/v1/upload/upload`, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }
      
      const result = await response.json();
      setUploadResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setUploadResult(null);
    setError(null);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h2 className="text-2xl font-semibold text-[#2C2C2A] mb-6">Upload Sales Data</h2>
      
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-[#2C2C2A] bg-[#F5F5F0]'
            : 'border-[#E5E5E0] hover:border-[#9C9C9A]'
        }`}
      >
        {!file ? (
          <>
            <div className="mx-auto w-16 h-16 bg-[#F5F5F0] rounded-full flex items-center justify-center mb-4">
              <Upload className="text-[#9C9C9A]" size={28} />
            </div>
            <p className="text-[#2C2C2A] font-medium mb-2">
              Drag and drop your file here
            </p>
            <p className="text-[#9C9C9A] text-sm mb-4">
              or click to browse from your computer
            </p>
            <p className="text-[#9C9C9A] text-xs">
              Supported: CSV, XLSX, XLS, TXT (Max 50MB)
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.xls,.txt"
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="inline-block mt-4 px-4 py-2 bg-[#2C2C2A] text-white text-sm font-medium rounded-lg cursor-pointer hover:bg-[#3C3C3A] transition-colors"
            >
              Select File
            </label>
          </>
        ) : (
          <div className="flex items-center justify-center gap-4">
            <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg border border-[#E5E5E0]">
              <FileText className="text-[#9C9C9A]" size={24} />
              <div className="text-left">
                <p className="text-sm font-medium text-[#2C2C2A]">{file.name}</p>
                <p className="text-xs text-[#9C9C9A]">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={clearFile}
                className="ml-4 p-1 hover:bg-[#F5F5F0] rounded transition-colors"
              >
                <X size={18} className="text-[#9C9C9A]" />
              </button>
            </div>
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="px-6 py-2 bg-[#2C2C2A] text-white text-sm font-medium rounded-lg hover:bg-[#3C3C3A] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload size={16} />
                  Upload
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3">
          <AlertCircle className="text-red-600" size={20} />
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      )}

      {/* Upload Results */}
      {uploadResult && (
        <div className="mt-8 space-y-6">
          {/* Success Header */}
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="text-green-600" size={24} />
            <div>
              <p className="font-medium text-green-800">File uploaded successfully!</p>
              <p className="text-sm text-green-600">
                {uploadResult.row_count.toLocaleString()} rows × {uploadResult.column_count} columns
              </p>
            </div>
          </div>

          {/* Validation Report */}
          <div className="bg-white rounded-xl border border-[#E5E5E0] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#F0F0EA]">
              <h3 className="font-semibold text-[#2C2C2A]">Validation Report</h3>
            </div>
            <div className="p-6">
              <div className="flex gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-sm text-[#6C6C6A]">
                    {uploadResult.validation.errors} Errors
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <span className="text-sm text-[#6C6C6A]">
                    {uploadResult.validation.warnings} Warnings
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm text-[#6C6C6A]">
                    {uploadResult.validation.infos} Info
                  </span>
                </div>
              </div>

              {uploadResult.validation.issues.length > 0 ? (
                <div className="space-y-2">
                  {uploadResult.validation.issues.map((issue, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border text-sm ${getSeverityColor(issue.severity)}`}
                    >
                      <p className="font-medium">{issue.message}</p>
                      <p className="mt-1 opacity-80">{issue.suggestion}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6C6C6A]">No issues found!</p>
              )}
            </div>
          </div>

          {/* Schema Detection */}
          <div className="bg-white rounded-xl border border-[#E5E5E0] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#F0F0EA]">
              <h3 className="font-semibold text-[#2C2C2A]">Detected Schema</h3>
              {uploadResult.schema.suggested_date_column && (
                <p className="text-sm text-[#6C6C6A] mt-1">
                  Date column: <span className="font-medium">{uploadResult.schema.suggested_date_column}</span>
                </p>
              )}
              {uploadResult.schema.suggested_sku_column && (
                <p className="text-sm text-[#6C6C6A] mt-1">
                  SKU column: <span className="font-medium">{uploadResult.schema.suggested_sku_column}</span>
                </p>
              )}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#FAFAF5]">
                  <tr>
                    <th className="px-6 py-3 text-left font-medium text-[#6C6C6A]">Column</th>
                    <th className="px-6 py-3 text-left font-medium text-[#6C6C6A]">Type</th>
                    <th className="px-6 py-3 text-left font-medium text-[#6C6C6A]">Suggested</th>
                    <th className="px-6 py-3 text-left font-medium text-[#6C6C6A]">Nulls</th>
                    <th className="px-6 py-3 text-left font-medium text-[#6C6C6A]">Sample</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F0EA]">
                  {uploadResult.schema.columns.map((col, idx) => (
                    <tr key={idx} className="hover:bg-[#FAFAF5]">
                      <td className="px-6 py-3 font-medium text-[#2C2C2A]">{col.name}</td>
                      <td className="px-6 py-3 text-[#6C6C6A]">{col.detected_type}</td>
                      <td className="px-6 py-3">
                        {col.suggested_mapping && (
                          <span className="px-2 py-1 bg-[#F5F5F0] text-[#2C2C2A] rounded-full text-xs">
                            {col.suggested_mapping}
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-3 text-[#6C6C6A]">
                        {col.null_count > 0 ? (
                          <span className="text-amber-600">
                            {col.null_percentage.toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-green-600">0%</span>
                        )}
                      </td>
                      <td className="px-6 py-3 text-[#9C9C9A] text-xs">
                        {col.sample_values.slice(0, 2).join(', ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Data Preview */}
          <div className="bg-white rounded-xl border border-[#E5E5E0] overflow-hidden">
            <div className="px-6 py-4 border-b border-[#F0F0EA]">
              <h3 className="font-semibold text-[#2C2C2A]">Data Preview</h3>
              <p className="text-sm text-[#6C6C6A]">First {uploadResult.preview.length} rows</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#FAFAF5]">
                  <tr>
                    {uploadResult.schema.columns.map((col, idx) => (
                      <th key={idx} className="px-4 py-3 text-left font-medium text-[#6C6C6A]">
                        {col.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F0F0EA]">
                  {uploadResult.preview.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-[#FAFAF5]">
                      {uploadResult.schema.columns.map((col, colIdx) => (
                        <td key={colIdx} className="px-4 py-3 text-[#2C2C2A]">
                          {row[col.name] !== null && row[col.name] !== undefined
                            ? String(row[col.name])
                            : '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              className="flex-1 px-6 py-3 bg-[#2C2C2A] text-white font-medium rounded-lg hover:bg-[#3C3C3A] transition-colors"
              onClick={() => {
                // TODO: Navigate to column mapping or processing
                console.log('Proceed with upload:', uploadResult.upload_id);
              }}
            >
              Process Data
            </button>
            <button
              className="px-6 py-3 border border-[#E5E5E0] text-[#6C6C6A] font-medium rounded-lg hover:bg-[#FAFAF5] transition-colors"
              onClick={clearFile}
            >
              Upload Another
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
