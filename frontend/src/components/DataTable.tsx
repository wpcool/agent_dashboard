import React from 'react';

interface DataTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  columns,
  rows,
  maxRows = 100,
}) => {
  const displayRows = rows.slice(0, maxRows);
  const hasMore = rows.length > maxRows;

  return (
    <div className="overflow-x-auto my-2">
      <table className="min-w-full bg-white border border-gray-200 text-sm">
        <thead>
          <tr className="bg-gray-50">
            {columns.map((col) => (
              <th
                key={col}
                className="px-4 py-2 border-b text-left font-medium text-gray-700"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayRows.map((row, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-4 py-2 border-b text-gray-600">
                  {row[col] === null ? (
                    <span className="text-gray-400">NULL</span>
                  ) : (
                    String(row[col])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasMore && (
        <div className="text-gray-500 text-xs mt-2">
          仅显示前 {maxRows} 行，共 {rows.length} 行
        </div>
      )}
    </div>
  );
};
