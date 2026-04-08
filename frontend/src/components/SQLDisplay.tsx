import React from 'react';

interface SQLDisplayProps {
  sql: string;
  executionTimeMs?: number;
  onCopy?: () => void;
}

export const SQLDisplay: React.FC<SQLDisplayProps> = ({
  sql,
  executionTimeMs,
  onCopy,
}) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    onCopy?.();
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 my-2">
      <div className="flex justify-between items-center mb-2">
        <span className="text-gray-400 text-xs">生成的 SQL</span>
        <button
          onClick={handleCopy}
          className="text-gray-400 hover:text-white text-xs"
        >
          复制
        </button>
      </div>
      <pre className="text-green-400 text-sm overflow-x-auto">
        <code>{sql}</code>
      </pre>
      {executionTimeMs !== undefined && (
        <div className="text-gray-500 text-xs mt-2">
          执行时间: {executionTimeMs}ms
        </div>
      )}
    </div>
  );
};
