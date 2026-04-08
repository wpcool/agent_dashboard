import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { ChartView } from './ChartView';
import { Send, Loader2, AlertTriangle, Database, BarChart3, Table, ChevronLeft, Copy, Check } from 'lucide-react';

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
  const [showChart, setShowChart] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
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

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const suggestions = [
    '查询昨天的销售额',
    '最近7天热销商品排行',
    '各城市订单量对比',
    'VIP客户消费分析',
  ];

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
        <div className="flex items-center gap-4">
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-1 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
              <span>返回</span>
            </button>
          )}
          <div>
            <h2 className="font-semibold text-gray-800">新对话</h2>
            <p className="text-sm text-gray-400">通用数据分析师</p>
          </div>
        </div>
        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
          <BarChart3 className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="text-6xl mb-4">👋</div>
            <p className="text-lg mb-2">开始一个新的对话</p>
            <p className="text-sm mb-6">试试以下问题：</p>
            <div className="flex flex-wrap justify-center gap-2 max-w-xl">
              {suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInput(suggestion);
                  }}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm text-gray-600 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-4xl mx-auto">
            {messages.map((message, idx) => (
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
                  className={`max-w-[85%] rounded-2xl px-5 py-4 ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

                  {/* SQL 展示 */}
                  {message.sql && (
                    <div className="mt-4 bg-gray-900 rounded-xl overflow-hidden">
                      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                        <div className="flex items-center gap-2">
                          <Database className="w-4 h-4 text-gray-400" />
                          <span className="text-xs text-gray-400 font-medium">SQL</span>
                        </div>
                        <button
                          onClick={() => copyToClipboard(message.sql!, `sql-${idx}`)}
                          className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors"
                        >
                          {copied === `sql-${idx}` ? (
                            <>
                              <Check className="w-3 h-3" />
                              已复制
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              复制
                            </>
                          )}
                        </button>
                      </div>
                      <div className="p-4 overflow-x-auto">
                        <code className="text-sm text-green-400 font-mono">
                          {message.sql}
                        </code>
                      </div>
                    </div>
                  )}

                  {/* 警告提示 */}
                  {message.needsVerification && (
                    <div className="mt-4 flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-700 text-sm">
                      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      <span>AI 对结果不是很有把握，建议核实</span>
                    </div>
                  )}

                  {/* 数据结果 */}
                  {message.results && message.results.length > 0 && (
                    <div className="mt-4">
                      {/* 切换按钮 */}
                      <div className="flex items-center gap-2 mb-3">
                        <button
                          onClick={() => setShowChart(prev => ({ ...prev, [idx]: false }))}
                          className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                            !showChart[idx]
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                          }`}
                        >
                          <Table className="w-4 h-4" />
                          表格
                        </button>
                        <button
                          onClick={() => setShowChart(prev => ({ ...prev, [idx]: true }))}
                          className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                            showChart[idx]
                              ? 'bg-blue-500 text-white'
                              : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                          }`}
                        >
                          <BarChart3 className="w-4 h-4" />
                          图表
                        </button>
                      </div>

                      {/* 表格视图 */}
                      {!showChart[idx] && (
                        <div className="overflow-x-auto bg-white rounded-xl border border-gray-200">
                          <table className="min-w-full text-sm">
                            <thead className="bg-gray-50">
                              <tr>
                                {Object.keys(message.results[0]).map((key) => (
                                  <th
                                    key={key}
                                    className="px-4 py-3 text-left font-medium text-gray-600 border-b"
                                  >
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.results.map((row, ridx) => (
                                <tr key={ridx} className="hover:bg-gray-50">
                                  {Object.values(row).map((value: any, vidx) => (
                                    <td key={vidx} className="px-4 py-3 border-b border-gray-100">
                                      {value}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* 图表视图 */}
                      {showChart[idx] && (
                        <div className="bg-white rounded-xl border border-gray-200 p-4">
                          <ChartView
                            data={message.results}
                            columns={Object.keys(message.results[0])}
                          />
                        </div>
                      )}
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
      <div className="p-4 border-t border-gray-100 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 bg-gray-100 rounded-2xl px-4 py-3 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:bg-white transition-all">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="输入你的问题，按 Enter 发送..."
              className="flex-1 bg-transparent outline-none text-gray-800 placeholder-gray-400"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
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
