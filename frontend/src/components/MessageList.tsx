import React from 'react';
import { Message } from '../types/chat';
import { MessageItem } from './MessageItem';

interface MessageListProps {
  messages: Message[];
  results?: Record<string, unknown>[];
  loading?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  results,
  loading,
}) => {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <MessageItem
          key={message.id}
          message={message}
          results={message.role === 'assistant' ? results : undefined}
        />
      ))}

      {loading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 rounded-lg p-4">
            <div className="flex space-x-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};
