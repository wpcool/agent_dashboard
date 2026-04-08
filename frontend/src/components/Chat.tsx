import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  contentType?: string;
  sql?: string;
  results?: any[];
  needsVerification?: boolean;
}

interface ChatProps {
  conversationId?: string;
  agentId?: string;
  onBack?: () => void;
}

export const Chat: React.FC<ChatProps> = ({ conversationId, agentId: _agentId, onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 如果有 conversationId，加载历史消息
    if (currentConversationId) {
      // TODO: 加载历史消息
    }
  }, [currentConversationId]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.post('/api/v1/chat', {
        message: input,
        conversation_id: currentConversationId,
      });

      const assistantMessage: Message = {
        id: response.data.message.id,
        role: 'assistant',
        content: response.data.message.content,
        sql: response.data.sql,
        results: response.data.results,
        needsVerification: response.data.needs_verification,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (!currentConversationId && response.data.message.conversation_id) {
        setCurrentConversationId(response.data.message.conversation_id);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: '抱歉，处理请求时出错，请稍后重试。',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              返回
            </button>
          )}
          <div>
            <h2 className="font-semibold text-gray-800">新对话</h2>
            <p className="text-sm text-gray-400">通用数据分析师</p>
          </div>
        </div>
        <button className="p-2 text-gray-400 hover:text-gray-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-6xl mb-4">👋</div>
            <p>开始一个新的对话</p>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gradient-to-br from-blue-100 to-purple-100'
                  }`}
                >
                  {message.role === 'user' ? '我' : '🤖'}
                </div>
                <div
                  className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>

                  {message.sql && (
                    <div className="mt-3 bg-gray-800 rounded-lg p-3 overflow-x-auto">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-gray-400">SQL</span>
                        <button
                          onClick={() => navigator.clipboard.writeText(message.sql!)}
                          className="text-xs text-blue-400 hover:text-blue-300"
                        >
                          复制
                        </button>
                      </div>
                      <code className="text-sm text-green-400 font-mono">
                        {message.sql}
                      </code>
                    </div>
                  )}

                  {message.needsVerification && (
                    <div className="mt-3 flex items-center gap-2 text-amber-600 text-sm">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      需要确认
                    </div>
                  )}

                  {message.results && message.results.length > 0 && (
                    <div className="mt-3 overflow-x-auto">
                      <table className="min-w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-200">
                            {Object.keys(message.results[0]).map((key) => (
                              <th key={key} className="px-3 py-2 text-left font-medium text-gray-600">
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {message.results.slice(0, 5).map((row, idx) => (
                            <tr key={idx} className="border-b border-gray-100">
                              {Object.values(row).map((value: any, vidx) => (
                                <td key={vidx} className="px-3 py-2">
                                  {value}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-100">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3 bg-gray-100 rounded-2xl px-4 py-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="输入你的问题..."
              className="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-2 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            AI 生成的内容可能存在错误，请谨慎使用
          </p>
        </div>
      </div>
    </div>
  );
};
