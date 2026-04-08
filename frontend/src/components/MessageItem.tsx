import React from 'react';
import { Message } from '../types/chat';
import { SQLDisplay } from './SQLDisplay';
import { DataTable } from './DataTable';

interface MessageItemProps {
  message: Message;
  results?: Record<string, unknown>[];
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  results,
}) => {
  const isUser = message.role === 'user';
  const metadata = message.execution_metadata;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg p-4 ${
          isUser
            ? 'bg-blue-500 text-white'
            : 'bg-white border border-gray-200 text-gray-800'
        }`}
      >
        {/* 消息内容 */}
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* SQL 展示 */}
        {!isUser && metadata?.sql && (
          <SQLDisplay
            sql={metadata.sql}
            executionTimeMs={metadata.query_result?.execution_time_ms}
          />
        )}

        {/* 数据表格 */}
        {!isUser && results && results.length > 0 && metadata?.query_result?.columns && (
          <DataTable
            columns={metadata.query_result.columns}
            rows={results}
          />
        )}

        {/* 验证提示 */}
        {!isUser && metadata?.needs_clarification && (
          <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm">
            需要确认
          </div>
        )}

        {/* 时间戳 */}
        <div
          className={`text-xs mt-2 ${
            isUser ? 'text-blue-100' : 'text-gray-400'
          }`}
        >
          {new Date(message.created_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};
