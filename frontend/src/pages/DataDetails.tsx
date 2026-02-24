import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Loader2, AlertCircle, AlertTriangle, Info, CheckCircle, TrendingUp, TrendingDown, DollarSign, Package } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

interface SalesPerformance {
  upload_id: string;
  period_days: number;
  date_range: {
    start: string;
    end: string;
  };
  total_sales: {
    units: number;
    revenue: number;
  };
  daily_sales: Array<{
    date: string;
    sku_id: string;
    total_units: number;
    total_revenue: number;
  }>;
  trend: {
    percentage: number;
    direction: string;
    current_period_revenue: number;
    previous_period_revenue: number;
  };
}

interface DailySalesAggregate {
  date: string;
  total_units: number;
  total_revenue: number;
}

interface ProductPerformance {
  upload_id: string;
  period_days: number;
  date_range: {
    start: string;
    end: string;
  };
  best_sellers: Array<{
    sku_id: string;
    total_units: number;
    total_revenue: number;
    avg_price: number;
  }>;
  slow_movers: Array<{
    sku_id: string;
    units_sold: number;
    stock_level: number;
    sell_through_rate: number;
  }>;
  dead_stock: Array<{
    sku_id: string;
    last_sale_date: string;
    days_since_sale: number;
    current_stock: number;
  }>;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function DataDetails() {
  const { id } = useParams<{ id: string }>();
  const [upload, setUpload] = useState<UploadDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedDays, setSelectedDays] = useState<number>(7);
  const [salesData, setSalesData] = useState<SalesPerformance | null>(null);
  const [salesLoading, setSalesLoading] = useState(false);
  const [salesError, setSalesError] = useState<string | null>(null);

  const [productDays, setProductDays] = useState<number>(7);
  const [productData, setProductData] = useState<ProductPerformance | null>(null);
  const [productLoading, setProductLoading] = useState(false);
  const [productError, setProductError] = useState<string | null>(null);

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
    const fetchSalesPerformance = async () => {
      if (!id) return;
      setSalesLoading(true);
      setSalesError(null);
      try {
        const response = await fetch(`${API_URL}/api/v1/metrics/${id}/sales?days=${selectedDays}`);
        if (!response.ok) {
          throw new Error('Failed to fetch sales performance');
        }
        const data = await response.json();
        setSalesData(data);
      } catch (err) {
        setSalesError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setSalesLoading(false);
      }
    };

    fetchSalesPerformance();
  }, [id, selectedDays]);

  useEffect(() => {
    const fetchProductPerformance = async () => {
      if (!id) return;
      setProductLoading(true);
      setProductError(null);
      try {
        const response = await fetch(`${API_URL}/api/v1/metrics/${id}/product?days=${productDays}`);
        if (!response.ok) {
          throw new Error('Failed to fetch product performance');
        }
        const data = await response.json();
        setProductData(data);
      } catch (err) {
        setProductError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setProductLoading(false);
      }
    };

    fetchProductPerformance();
  }, [id, productDays]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'processing':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'error':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const aggregateDailySales = (dailySales: SalesPerformance['daily_sales']): DailySalesAggregate[] => {
    const aggregated = dailySales.reduce((acc, sale) => {
      const date = sale.date;
      if (!acc[date]) {
        acc[date] = { date, total_units: 0, total_revenue: 0 };
      }
      acc[date].total_units += sale.total_units;
      acc[date].total_revenue += sale.total_revenue;
      return acc;
    }, {} as Record<string, DailySalesAggregate>);
    
    return Object.values(aggregated).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

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

      {/* Title */}
      <h1 className="text-2xl font-semibold text-[#2C2C2A] mb-3">
        {upload.filename}
      </h1>

      {/* Upload Details Pills */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium border ${getStatusColor(upload.status)}`}>
          {upload.status}
        </span>
        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-[#F5F5F0] text-[#6C6C6A] border border-[#E5E5E0]">
          {upload.row_count.toLocaleString()} rows
        </span>
        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-[#F5F5F0] text-[#6C6C6A] border border-[#E5E5E0]">
          {upload.column_count} columns
        </span>
        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-[#F5F5F0] text-[#6C6C6A] border border-[#E5E5E0]">
          Uploaded {new Date(upload.uploaded_at).toLocaleDateString()}
        </span>
        {upload.processed_at && (
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-[#F5F5F0] text-[#6C6C6A] border border-[#E5E5E0]">
            Processed {new Date(upload.processed_at).toLocaleDateString()}
          </span>
        )}
      </div>

      {/* Validation Summary Pills */}
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3">
          {upload.validation.is_valid ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-green-100 text-green-700 border border-green-200">
              <CheckCircle size={14} />
              Valid
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-red-100 text-red-700 border border-red-200">
              <AlertCircle size={14} />
              Invalid
            </span>
          )}
          
          {upload.validation.total_issues > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-gray-100 text-gray-700 border border-gray-200">
              <Info size={14} />
              {upload.validation.total_issues} issues
            </span>
          )}
          
          {upload.validation.errors > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-red-100 text-red-700 border border-red-200">
              <AlertCircle size={14} />
              {upload.validation.errors} errors
            </span>
          )}
          
          {upload.validation.warnings > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-amber-100 text-amber-700 border border-amber-200">
              <AlertTriangle size={14} />
              {upload.validation.warnings} warnings
            </span>
          )}
          
          {upload.validation.infos > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-blue-100 text-blue-700 border border-blue-200">
              <Info size={14} />
              {upload.validation.infos} info
            </span>
          )}
        </div>
        
        {upload.validation.summary && (
          <p className="text-sm text-[#6C6C6A] mt-3">
            {upload.validation.summary}
          </p>
        )}
      </div>

      {/* Sales Performance Section */}
      <div className="mt-8 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#2C2C2A]">
            Sales Performance
          </h2>
          <select
            value={selectedDays}
            onChange={(e) => setSelectedDays(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-[#E5E5E0] bg-white text-sm text-[#2C2C2A] focus:outline-none focus:ring-2 focus:ring-[#2C2C2A]"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>

        {salesLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin text-[#9C9C9A]" size={32} />
          </div>
        ) : salesError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
            Error loading sales performance: {salesError}
          </div>
        ) : salesData ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Card - Total Sales & Trend */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <h3 className="text-sm font-medium text-[#6C6C6A] mb-4">Total Sales</h3>
              
              <div className="space-y-6">
                {/* Revenue */}
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-green-100">
                    <DollarSign className="text-green-600" size={24} />
                  </div>
                  <div>
                    <p className="text-2xl font-semibold text-[#2C2C2A]">
                      ${salesData.total_sales.revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                    <p className="text-sm text-[#6C6C6A]">Total Revenue</p>
                  </div>
                </div>

                {/* Units */}
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-blue-100">
                    <Package className="text-blue-600" size={24} />
                  </div>
                  <div>
                    <p className="text-2xl font-semibold text-[#2C2C2A]">
                      {salesData.total_sales.units.toLocaleString()}
                    </p>
                    <p className="text-sm text-[#6C6C6A]">Units Sold</p>
                  </div>
                </div>

                {/* Trend */}
                <div className="pt-4 border-t border-[#E5E5E0]">
                  <div className="flex items-center gap-2">
                    {salesData.trend.direction === 'up' ? (
                      <>
                        <TrendingUp className="text-green-600" size={20} />
                        <span className="text-green-600 font-medium">+{salesData.trend.percentage.toFixed(2)}%</span>
                      </>
                    ) : salesData.trend.direction === 'down' ? (
                      <>
                        <TrendingDown className="text-red-600" size={20} />
                        <span className="text-red-600 font-medium">{salesData.trend.percentage.toFixed(2)}%</span>
                      </>
                    ) : (
                      <span className="text-[#6C6C6A] font-medium">0%</span>
                    )}
                    <span className="text-sm text-[#6C6C6A]">vs previous period</span>
                  </div>
                  <p className="text-xs text-[#9C9C9A] mt-1">
                    {new Date(salesData.date_range.start).toLocaleDateString()} - {new Date(salesData.date_range.end).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>

            {/* Right Card - Daily Sales Chart */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <h3 className="text-sm font-medium text-[#6C6C6A] mb-4">Daily Sales Trend</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={aggregateDailySales(salesData.daily_sales)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E5E0" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(date: string) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      stroke="#6C6C6A"
                      fontSize={12}
                    />
                    <YAxis 
                      stroke="#6C6C6A"
                      fontSize={12}
                      tickFormatter={(value: number) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip 
                      formatter={(value) => [`$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`, 'Revenue']}
                      labelFormatter={(label) => new Date(String(label)).toLocaleDateString()}
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #E5E5E0', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="total_revenue" 
                      stroke="#2C2C2A" 
                      strokeWidth={2}
                      dot={{ fill: '#2C2C2A', strokeWidth: 0, r: 4 }}
                      activeDot={{ r: 6, fill: '#2C2C2A' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Product Performance Section */}
      <div className="mt-8 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-[#2C2C2A]">
            Product Performance
          </h2>
          <select
            value={productDays}
            onChange={(e) => setProductDays(Number(e.target.value))}
            className="px-3 py-2 rounded-lg border border-[#E5E5E0] bg-white text-sm text-[#2C2C2A] focus:outline-none focus:ring-2 focus:ring-[#2C2C2A]"
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>

        {productLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="animate-spin text-[#9C9C9A]" size={32} />
          </div>
        ) : productError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
            Error loading product performance: {productError}
          </div>
        ) : productData ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Best Sellers Card */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <h3 className="text-sm font-medium text-[#6C6C6A] mb-4 flex items-center gap-2">
                <TrendingUp size={16} className="text-green-600" />
                Best Sellers
              </h3>
              {productData.best_sellers.length > 0 ? (
                <div className="space-y-4">
                  {productData.best_sellers.map((product, index) => (
                    <div key={product.sku_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-[#F5F5F0] text-xs font-medium text-[#6C6C6A]">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-[#2C2C2A]">{product.sku_id}</p>
                          <p className="text-xs text-[#6C6C6A]">{product.total_units.toLocaleString()} units</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-[#2C2C2A]">
                          ${product.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </p>
                        <p className="text-xs text-[#6C6C6A]">avg ${product.avg_price.toFixed(2)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6C6C6A] text-center py-4">No best sellers data</p>
              )}
            </div>

            {/* Slow Movers Card */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <h3 className="text-sm font-medium text-[#6C6C6A] mb-4 flex items-center gap-2">
                <TrendingDown size={16} className="text-amber-600" />
                Slow Movers
              </h3>
              {productData.slow_movers.length > 0 ? (
                <div className="space-y-4">
                  {productData.slow_movers.map((product) => (
                    <div key={product.sku_id} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-[#2C2C2A]">{product.sku_id}</p>
                        <p className="text-xs text-[#6C6C6A]">
                          {product.units_sold.toLocaleString()} sold / {product.stock_level.toLocaleString()} in stock
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-amber-600">
                          {product.sell_through_rate.toFixed(1)}%
                        </p>
                        <p className="text-xs text-[#6C6C6A]">sell-through</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6C6C6A] text-center py-4">No slow movers detected</p>
              )}
            </div>

            {/* Dead Stock Card */}
            <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] p-6">
              <h3 className="text-sm font-medium text-[#6C6C6A] mb-4 flex items-center gap-2">
                <AlertCircle size={16} className="text-red-600" />
                Dead Stock
              </h3>
              {productData.dead_stock.length > 0 ? (
                <div className="space-y-4">
                  {productData.dead_stock.map((product) => (
                    <div key={product.sku_id} className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-[#2C2C2A]">{product.sku_id}</p>
                        <p className="text-xs text-[#6C6C6A]">
                          Last sale: {new Date(product.last_sale_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-red-600">
                          {product.days_since_sale} days
                        </p>
                        <p className="text-xs text-[#6C6C6A]">
                          {product.current_stock.toLocaleString()} in stock
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[#6C6C6A] text-center py-4">No dead stock detected</p>
              )}
            </div>
          </div>
        ) : null}
      </div>

      {/* Validation Issues List */}
      {upload.validation.issues.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] overflow-hidden">
          <div className="px-6 py-4 border-b border-[#E5E5E0]">
            <h2 className="text-lg font-semibold text-[#2C2C2A]">
              Validation Issues
            </h2>
          </div>
          <div className="divide-y divide-[#E5E5E0]">
            {upload.validation.issues.map((issue, index) => (
              <div key={index} className="px-6 py-4">
                <div className="flex items-start gap-3">
                  {issue.severity === 'error' && (
                    <AlertCircle className="text-red-500 mt-0.5" size={16} />
                  )}
                  {issue.severity === 'warning' && (
                    <AlertTriangle className="text-amber-500 mt-0.5" size={16} />
                  )}
                  {issue.severity === 'info' && (
                    <Info className="text-blue-500 mt-0.5" size={16} />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-[#2C2C2A]">
                      {issue.message}
                    </p>
                    {issue.suggestion && (
                      <p className="text-sm text-[#6C6C6A] mt-1">
                        {issue.suggestion}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-[#F5F5F0] text-[#6C6C6A]">
                        {issue.type}
                      </span>
                      {issue.column && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-[#F5F5F0] text-[#6C6C6A]">
                          Column: {issue.column}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
