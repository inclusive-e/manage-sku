import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle,
  Loader2,
} from 'lucide-react';

interface ValidationIssue {
  severity: string;
  type: string;
  column?: string;
  message: string;
  suggestion: string;
}

interface Validation {
  is_valid: boolean;
  total_issues: number;
  errors: number;
  warnings: number;
  infos: number;
  issues: ValidationIssue[];
  summary: string;
}

interface Upload {
  upload_id: string;
  filename: string;
  status: string;
  row_count: number;
  column_count: number;
  uploaded_at: string;
  processed_at: string | null;
  validation: Validation;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ValidationIcon = ({ validation }: { validation: Validation }) => {
  if (validation.errors > 0) {
    return (
      <div className="group relative">
        <AlertCircle className="text-red-500" size={20} />
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded-lg z-10">
          {validation.summary}
        </div>
      </div>
    );
  }
  if (validation.warnings > 0) {
    return (
      <div className="group relative">
        <AlertTriangle className="text-amber-500" size={20} />
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded-lg z-10">
          {validation.summary}
        </div>
      </div>
    );
  }
  if (validation.infos > 0) {
    return (
      <div className="group relative">
        <Info className="text-blue-500" size={20} />
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded-lg z-10">
          {validation.summary}
        </div>
      </div>
    );
  }
  return (
    <div className="group relative">
      <CheckCircle className="text-green-500" size={20} />
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-2 bg-gray-900 text-white text-xs rounded-lg z-10">
        {validation.summary}
      </div>
    </div>
  );
};

const StatusBadge = ({ status }: { status: string }) => {
  const statusColors: Record<string, string> = {
    uploaded: 'bg-gray-100 text-gray-600',
    processing: 'bg-blue-100 text-blue-600',
    processed: 'bg-green-100 text-green-600',
    error: 'bg-red-100 text-red-600',
  };

  return (
    <span
      className={`px-2 py-1 rounded-full text-xs font-medium ${
        statusColors[status] || 'bg-gray-100 text-gray-600'
      }`}
    >
      {status}
    </span>
  );
};

export function Data() {
  const [uploads, setUploads] = useState<Upload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUploads = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/upload/uploads`);
        if (!response.ok) {
          throw new Error('Failed to fetch uploads');
        }
        const data = await response.json();
        setUploads(data.uploads || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchUploads();
  }, []);

  const columns = useMemo<ColumnDef<Upload>[]>(
    () => [
      {
        accessorKey: 'filename',
        header: 'Filename',
        cell: (info) => (
          <span className="text-sm font-medium text-[#2C2C2A]">
            {info.getValue() as string}
          </span>
        ),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: (info) => <StatusBadge status={info.getValue() as string} />,
      },
      {
        accessorKey: 'row_count',
        header: 'Rows',
        cell: (info) => (
          <span className="text-sm text-[#6C6C6A]">
            {(info.getValue() as number).toLocaleString()}
          </span>
        ),
      },
      {
        accessorKey: 'uploaded_at',
        header: 'Uploaded',
        cell: (info) => (
          <span className="text-sm text-[#6C6C6A]">
            {new Date(info.getValue() as string).toLocaleString()}
          </span>
        ),
      },
      {
        accessorKey: 'validation',
        header: 'Validation',
        cell: (info) => (
          <ValidationIcon validation={info.getValue() as Validation} />
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data: uploads,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#9C9C9A]" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
          Error loading uploads: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-[#2C2C2A]">Data Uploads</h1>
        <span className="text-sm text-[#9C9C9A]">
          {uploads.length} upload{uploads.length !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-[#E5E5E0] overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#FAFAF5]">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3.5 text-left text-xs font-medium text-[#6C6C6A] uppercase tracking-wide"
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-[#F0F0EA]">
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-8 text-center text-[#9C9C9A]"
                >
                  No uploads yet. Upload a file to get started.
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => (
                <tr 
                  key={row.id} 
                  className="hover:bg-[#FAFAF5] cursor-pointer"
                  onClick={() => navigate(`/data/${row.original.upload_id}`)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-6 py-4">
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {table.getPageCount() > 1 && (
          <div className="px-6 py-3 border-t border-[#F0F0EA] flex items-center justify-between">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1 text-sm text-[#6C6C6A] hover:text-[#2C2C2A] disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-[#9C9C9A]">
              Page {table.getState().pagination.pageIndex + 1} of{' '}
              {table.getPageCount()}
            </span>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1 text-sm text-[#6C6C6A] hover:text-[#2C2C2A] disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
