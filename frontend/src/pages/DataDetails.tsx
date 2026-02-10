import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, FileText, DollarSign, Package, Tag, Calendar } from 'lucide-react';

interface UploadDetails {
  upload_id: string;
  filename: string;
  status: string;
  row_count: number;
  column_count: number;
  uploaded_at: string;
  processed_at: string | null;
  schema: Record<string, unknown>;
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
}

interface SalesData {
  id: number;
  upload_id: string;
  date: string;
  sku_id: string;
  sales_quantity: number;
  sales_revenue: number;
  stock_level: number | null;
  category: string | null;
  unit_price: number | null;
  created_at: string;
}

interface SalesSummary {
  upload_id: string;
  total_records: number;
  summary: {
    total_quantity: number;
    total_revenue: number;
    average_quantity: number;
    average_revenue: number;
    unique_skus: number;
  };
  date_range: {
    start: string;
    end: string;
  };
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function DataDetails() {
  const { id } = useParams<{ id: string }>();
  const [upload, setUpload] = useState<UploadDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SalesSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [sales, setSales] = useState<SalesData[]>([]);
  const [salesLoading, setSalesLoading] = useState(false);
  const [salesError, setSalesError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUploadDetails = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/upload/uploads/${id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch upload details');
        }
        const data = await response.json();
        setUpload(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchUploadDetails();
  }, [id]);

  useEffect(() => {
    const fetchSalesSummary = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/sales/uploads/${id}/sales/summary`);
        if (!response.ok) {
          throw new Error('Failed to fetch sales summary');
        }
        const data = await response.json();
        setSummary(data);
      } catch (err) {
        setSummaryError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setSummaryLoading(false);
      }
    };

    fetchSalesSummary();
  }, [id]);

  useEffect(() => {
    const fetchSales = async () => {
      setSalesLoading(true);
      try {
        const response = await fetch(`${API_URL}/api/v1/sales/uploads/${id}/sales`);
        if (!response.ok) {
          throw new Error('Failed to fetch sales data');
        }
        const data = await response.json();
        setSales(data.sales);
      } catch (err) {
        setSalesError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setSalesLoading(false);
      }
    };

    if (id) {
      fetchSales();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#9C9C9A]" size={32} />
      </div>
    );
  }

  if (error || !upload) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
          Error loading upload details: {error || 'Not found'}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Link
        to="/data"
        className="inline-flex items-center gap-2 text-sm text-[#6C6C6A] hover:text-[#2C2C2A] mb-6"
      >
        <ArrowLeft size={16} />
        Back to Data
      </Link>

      <h1 className="text-2xl font-semibold text-[#2C2C2A] mb-6">
        {upload.filename}
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <h2 className="text-lg font-semibold text-[#2C2C2A] mb-4">
            Upload Details
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-sm text-[#9C9C9A]">Upload ID</dt>
              <dd className="text-sm text-[#2C2C2A] font-mono">{upload.upload_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-[#9C9C9A]">Status</dt>
              <dd className="text-sm text-[#2C2C2A]">{upload.status}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-[#9C9C9A]">Rows</dt>
              <dd className="text-sm text-[#2C2C2A]">{upload.row_count.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-[#9C9C9A]">Columns</dt>
              <dd className="text-sm text-[#2C2C2A]">{upload.column_count}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-sm text-[#9C9C9A]">Uploaded At</dt>
              <dd className="text-sm text-[#2C2C2A]">
                {new Date(upload.uploaded_at).toLocaleString()}
              </dd>
            </div>
            {upload.processed_at && (
              <div className="flex justify-between">
                <dt className="text-sm text-[#9C9C9A]">Processed At</dt>
                <dd className="text-sm text-[#2C2C2A]">
                  {new Date(upload.processed_at).toLocaleString()}
                </dd>
              </div>
            )}
          </dl>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
          <h2 className="text-lg font-semibold text-[#2C2C2A] mb-4">
            Validation Summary
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9C9C9A]">Valid</span>
              <span
                className={`text-sm font-medium ${
                  upload.validation.is_valid ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {upload.validation.is_valid ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9C9C9A]">Total Issues</span>
              <span className="text-sm text-[#2C2C2A]">
                {upload.validation.total_issues}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9C9C9A]">Errors</span>
              <span className="text-sm text-red-600">
                {upload.validation.errors}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9C9C9A]">Warnings</span>
              <span className="text-sm text-amber-600">
                {upload.validation.warnings}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[#9C9C9A]">Infos</span>
              <span className="text-sm text-blue-600">
                {upload.validation.infos}
              </span>
            </div>
            <p className="text-sm text-[#6C6C6A] mt-4 pt-4 border-t border-[#F0F0EA]">
              {upload.validation.summary}
            </p>
          </div>
        </div>
      </div>

      {summaryLoading ? (
        <div className="mt-8 flex items-center justify-center h-32">
          <Loader2 className="animate-spin text-[#9C9C9A]" size={24} />
        </div>
      ) : summaryError ? (
        <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-4 text-red-600 text-sm">
          Error loading sales summary: {summaryError}
        </div>
      ) : summary ? (
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-[#2C2C2A] mb-4">
            Sales Summary
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <div className="flex items-center gap-3 mb-2">
                <FileText className="text-[#9C9C9A]" size={20} />
                <h3 className="text-sm text-[#6C6C6A]">Total Records</h3>
              </div>
              <p className="text-2xl font-semibold text-[#2C2C2A]">
                {summary.total_records.toLocaleString()}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign className="text-[#9C9C9A]" size={20} />
                <h3 className="text-sm text-[#6C6C6A]">Total Revenue</h3>
              </div>
              <p className="text-2xl font-semibold text-[#2C2C2A]">
                ${summary.summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <div className="flex items-center gap-3 mb-2">
                <Package className="text-[#9C9C9A]" size={20} />
                <h3 className="text-sm text-[#6C6C6A]">Total Quantity</h3>
              </div>
              <p className="text-2xl font-semibold text-[#2C2C2A]">
                {summary.summary.total_quantity.toLocaleString()}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <div className="flex items-center gap-3 mb-2">
                <Tag className="text-[#9C9C9A]" size={20} />
                <h3 className="text-sm text-[#6C6C6A]">Unique SKUs</h3>
              </div>
              <p className="text-2xl font-semibold text-[#2C2C2A]">
                {summary.summary.unique_skus.toLocaleString()}
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <div className="flex items-center gap-3 mb-2">
                <Calendar className="text-[#9C9C9A]" size={20} />
                <h3 className="text-sm text-[#6C6C6A]">Date Range</h3>
              </div>
              <p className="text-lg font-semibold text-[#2C2C2A]">
                {new Date(summary.date_range.start).toLocaleDateString()} - {new Date(summary.date_range.end).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-[#2C2C2A] mb-4">
          Sales Records
        </h2>

        {salesLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="animate-spin text-[#9C9C9A]" size={24} />
          </div>
        ) : salesError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
            Error loading sales data: {salesError}
          </div>
        ) : sales.length === 0 ? (
          <div className="bg-[#F5F5F0] rounded-lg p-8 text-center text-[#6C6C6A]">
            No sales records available.
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] overflow-hidden">
            <table className="w-full">
              <thead className="bg-[#F5F5F0]">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">SKU</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">Quantity</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">Revenue</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">Stock</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-[#2C2C2A]">Category</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E5E0]">
                {sales.map((sale) => (
                  <tr key={sale.id} className="hover:bg-[#F5F5F0]">
                    <td className="px-4 py-3 text-sm text-[#2C2C2A]">
                      {new Date(sale.date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#2C2C2A] font-mono">
                      {sale.sku_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#2C2C2A]">
                      {sale.sales_quantity}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#2C2C2A]">
                      ${sale.sales_revenue.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#2C2C2A]">
                      {sale.stock_level ?? '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-[#2C2C2A]">
                      {sale.category ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
