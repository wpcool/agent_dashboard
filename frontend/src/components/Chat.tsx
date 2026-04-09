import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api/client';
import { ChartView } from './ChartView';
import { Send, Loader2, AlertTriangle, Database, BarChart3, Table, ChevronLeft, Copy, Check, Sparkles, Lightbulb, ShieldCheck, ShieldAlert, Radio, Wifi } from 'lucide-react';

interface DataSource {
  id: string;
  name: string;
  type: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  contentType?: string;
  sql?: string;
  results?: any[];
  needsVerification?: boolean;
  // 智能分析模式字段
  analysisMode?: boolean;
  agentName?: string;
  analysisSteps?: {
    description: string;
    purpose: string;
    sql: string;
    insight: string;
    validation?: {
      is_valid: boolean;
      errors: string[];
      warnings: string[];
    };
  }[];
  stepsCompleted?: number;
  totalSteps?: number;
  recommendations?: string[];
  confidence?: number;
  validationSummary?: {
    total_steps: number;
    steps_with_errors: number;
    steps_with_warnings: number;
  };
}

interface ChatProps {
  conversationId?: string;
  agentId?: string;
  initialMessage?: string;
  onBack?: () => void;
}

export const Chat: React.FC<ChatProps> = ({ conversationId, agentId: _agentId, initialMessage, onBack }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | undefined>(conversationId);
  const [showChart, setShowChart] = useState<Record<string, boolean>>({});
  const [copied, setCopied] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const [streamingSteps, setStreamingSteps] = useState<{step_number: number, description: string, status: 'running' | 'complete' | 'error'}[]>([]);
  const [useStreaming, setUseStreaming] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialMessageSent = useRef(false);

  // 数据源选择
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');

  // 智能体信息
  const [currentAgent, setCurrentAgent] = useState<{id: string, name: string, code: string} | null>(null);

  // 加载智能体信息
  useEffect(() => {
    if (_agentId) {
      fetchAgentInfo(_agentId);
    }
  }, [_agentId]);

  const fetchAgentInfo = async (agentId: string) => {
    try {
      const response = await api.get(`/api/v1/agents/${agentId}`);
      setCurrentAgent({
        id: response.data.id,
        name: response.data.name,
        code: response.data.code
      });
    } catch (error) {
      console.error('Failed to fetch agent info:', error);
    }
  };

  // 加载数据源列表
  useEffect(() => {
    fetchDataSources();
  }, []);

  const fetchDataSources = async () => {
    try {
      const response = await api.get('/api/v1/data-sources');
      setDataSources(response.data);
      // 默认选择第一个
      if (response.data.length > 0 && !selectedDataSource) {
        setSelectedDataSource(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 加载历史消息
  useEffect(() => {
    if (currentConversationId) {
      fetchConversationHistory(currentConversationId);
    }
  }, [currentConversationId]);

  const fetchConversationHistory = async (convId: string) => {
    try {
      const response = await api.get(`/api/v1/conversations/${convId}/messages`);
      const historyMessages: Message[] = response.data.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        contentType: msg.content_type,
        sql: msg.execution_metadata?.sql,
        results: msg.execution_metadata?.query_result?.rows,
        needsVerification: msg.execution_metadata?.needs_verification,
        analysisMode: msg.content_type === 'analysis_report',
        agentName: msg.execution_metadata?.agent_name,
        analysisSteps: msg.execution_metadata?.steps_detail,
        stepsCompleted: msg.execution_metadata?.steps_completed,
        totalSteps: msg.execution_metadata?.total_steps,
        recommendations: msg.execution_metadata?.recommendations,
        confidence: msg.execution_metadata?.confidence,
        validationSummary: msg.execution_metadata?.validation_summary,
      }));
      setMessages(historyMessages);
    } catch (error) {
      console.error('Failed to load conversation history:', error);
    }
  };

  // 流式发送消息
  const handleSendMessageStream = async (messageToSend: string) => {
    if (!messageToSend.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setStreamingSteps([]);

    // 创建临时的助手消息
    const tempAssistantId = (Date.now() + 1).toString();
    const tempAssistantMessage: Message = {
      id: tempAssistantId,
      role: 'assistant',
      content: '正在分析...',
      analysisMode: currentAgent ? true : false,
      agentName: currentAgent?.name,
    };
    setStreamingMessage(tempAssistantMessage);
    setMessages((prev) => [...prev, tempAssistantMessage]);

    try {
      const response = await fetch(`${(import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          message: messageToSend,
          conversation_id: currentConversationId,
          data_source_id: selectedDataSource || undefined,
          agent_id: currentAgent?.id || undefined,
        }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let finalMessage: Message | null = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'conversation_created':
                  setCurrentConversationId(data.conversation_id);
                  break;

                case 'mode':
                  setStreamingMessage((prev) =>
                    prev
                      ? {
                          ...prev,
                          analysisMode: data.mode === 'intelligent',
                          agentName: data.agent_name,
                        }
                      : null
                  );
                  break;

                case 'plan_complete':
                  setStreamingMessage((prev) =>
                    prev
                      ? {
                          ...prev,
                          totalSteps: data.total_steps,
                          stepsCompleted: 0,
                        }
                      : null
                  );
                  break;

                case 'step_start':
                  const stepNum = Number(data.step_number || data.step || 1);
                  console.log('[SSE] step_start:', stepNum, data.description);
                  setStreamingSteps((prev) => {
                    // 避免重复添加同一步骤
                    if (prev.some(s => s.step_number === stepNum)) {
                      return prev;
                    }
                    return [
                      ...prev,
                      {
                        step_number: stepNum,
                        description: data.description || data.message || '分析中...',
                        status: 'running',
                      },
                    ];
                  });
                  break;

                case 'step_progress':
                  // 更新步骤状态
                  break;

                case 'step_complete':
                  const completeStepNum = Number(data.step_number);
                  console.log('[SSE] step_complete:', completeStepNum);
                  setStreamingSteps((prev) =>
                    prev.map((s) =>
                      s.step_number === completeStepNum ? { ...s, status: 'complete' } : s
                    )
                  );
                  break;

                case 'data':
                  setStreamingMessage((prev) =>
                    prev
                      ? {
                          ...prev,
                          content: `查询完成，返回 ${data.row_count} 条数据`,
                        }
                      : null
                  );
                  break;

                case 'complete':
                  finalMessage = {
                    id: tempAssistantId,
                    role: 'assistant',
                    content: data.message,
                    contentType: data.recommendations ? 'analysis_report' : 'text',
                    sql: data.sql,
                    results: data.results,
                    analysisMode: !!data.recommendations,
                    agentName: currentAgent?.name,
                    stepsCompleted: streamingSteps.filter((s) => s.status === 'complete').length,
                    totalSteps: streamingSteps.length,
                    recommendations: data.recommendations,
                    confidence: data.confidence,
                  };

                  // 更新最终消息
                  setMessages((prev) =>
                    prev.map((m) => (m.id === tempAssistantId ? finalMessage! : m))
                  );
                  setStreamingMessage(null);
                  break;

                case 'error':
                  setStreamingMessage((prev) =>
                    prev
                      ? {
                          ...prev,
                          content: `处理失败: ${data.message}`,
                        }
                      : null
                  );
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error);
      setStreamingMessage((prev) =>
        prev
          ? {
              ...prev,
              content: '抱歉，处理请求时出错，请稍后重试。',
            }
          : null
      );
    } finally {
      setIsLoading(false);
      setStreamingMessage(null);
    }
  };

  // 处理发送消息的内部函数
  const handleSendMessage = async (messageToSend: string) => {
    if (!messageToSend.trim() || isLoading) return;

    // 流式模式
    if (useStreaming) {
      await handleSendMessageStream(messageToSend);
      return;
    }

    // 非流式模式（原逻辑）
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    setIsLoading(true);

    try {
      const response = await api.post('/api/v1/chat', {
        message: messageToSend,
        conversation_id: currentConversationId,
        data_source_id: selectedDataSource || undefined,
        agent_id: currentAgent?.id || undefined,
      });

      const isAnalysisMode = response.data.message.content_type === 'analysis_report';
      const metadata = response.data.message.execution_metadata || {};

      const assistantMessage: Message = {
        id: response.data.message.id,
        role: 'assistant',
        content: response.data.message.content,
        contentType: response.data.message.content_type,
        sql: response.data.sql,
        results: response.data.results,
        needsVerification: response.data.needs_verification,
        // 智能分析模式字段
        analysisMode: isAnalysisMode,
        agentName: metadata.agent_name,
        analysisSteps: metadata.steps_detail,
        stepsCompleted: metadata.steps_completed,
        totalSteps: metadata.total_steps,
        recommendations: metadata.recommendations,
        confidence: metadata.confidence,
        validationSummary: metadata.validation_summary,
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

  // 自动发送初始消息 - 等待数据源加载完成后发送
  useEffect(() => {
    if (!initialMessage || initialMessageSent.current || dataSources.length === 0) return;

    initialMessageSent.current = true;

    const sendInitialMessage = async () => {
      const dsId = selectedDataSource || dataSources[0]?.id;

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: initialMessage,
      };

      setMessages([userMessage]);

      try {
        const response = await api.post('/api/v1/chat', {
          message: initialMessage,
          data_source_id: dsId,
          agent_id: currentAgent?.id || undefined,
        });

        const isAnalysisMode = response.data.message.content_type === 'analysis_report';
        const metadata = response.data.message.execution_metadata || {};

        const assistantMessage: Message = {
          id: response.data.message.id,
          role: 'assistant',
          content: response.data.message.content,
          contentType: response.data.message.content_type,
          sql: response.data.sql,
          results: response.data.results,
          needsVerification: response.data.needs_verification,
          analysisMode: isAnalysisMode,
          agentName: metadata.agent_name,
          analysisSteps: metadata.steps_detail,
          stepsCompleted: metadata.steps_completed,
          totalSteps: metadata.total_steps,
          recommendations: metadata.recommendations,
          confidence: metadata.confidence,
          validationSummary: metadata.validation_summary,
        };

        setMessages([userMessage, assistantMessage]);

        if (response.data.message.conversation_id) {
          setCurrentConversationId(response.data.message.conversation_id);
        }
      } catch (error) {
        setMessages([
          userMessage,
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: '抱歉，处理请求时出错，请稍后重试。',
          },
        ]);
      }
    };

    sendInitialMessage();
  }, [initialMessage, dataSources, selectedDataSource]);

  const handleSend = async () => {
    await handleSendMessage(input);
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
            <div className="flex items-center gap-2">
              <p className="text-sm text-gray-400">{currentAgent?.name || '通用数据分析师'}</p>
              {useStreaming && (
                <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                  <Radio className="w-3 h-3" />
                  实时
                </span>
              )}
            </div>
          </div>
          {/* 数据源选择器 */}
          {dataSources.length > 0 && (
            <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-200">
              <Database className="w-4 h-4 text-gray-400" />
              <select
                value={selectedDataSource}
                onChange={(e) => setSelectedDataSource(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:border-blue-400"
              >
                {dataSources.map((ds) => (
                  <option key={ds.id} value={ds.id}>
                    {ds.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setUseStreaming(!useStreaming)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              useStreaming
                ? 'bg-green-50 text-green-600 hover:bg-green-100'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
            title={useStreaming ? '实时流式输出已开启' : '点击开启实时流式输出'}
          >
            {useStreaming ? <Radio className="w-4 h-4" /> : <Wifi className="w-4 h-4" />}
            {useStreaming ? '实时' : '批量'}
          </button>
          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <BarChart3 className="w-5 h-5" />
          </button>
        </div>
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

                  {/* 流式传输状态 */}
                  {streamingMessage?.id === message.id && streamingSteps.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center gap-2 text-sm text-blue-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>分析进行中...</span>
                      </div>
                      <div className="space-y-1">
                        {streamingSteps.map((step) => (
                          <div
                            key={step.step_number}
                            className={`flex items-center gap-2 text-sm px-3 py-1.5 rounded ${
                              step.status === 'running'
                                ? 'bg-blue-50 text-blue-700'
                                : step.status === 'complete'
                                ? 'bg-green-50 text-green-700'
                                : 'bg-red-50 text-red-700'
                            }`}
                          >
                            {step.status === 'running' ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : step.status === 'complete' ? (
                              <Check className="w-3 h-3" />
                            ) : (
                              <AlertTriangle className="w-3 h-3" />
                            )}
                            <span className="font-medium">步骤 {step.step_number}:</span>
                            <span className="truncate">{step.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 智能分析模式标识 */}
                  {message.analysisMode && (
                    <div className="mt-4 flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-100 rounded-lg">
                      <Sparkles className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-blue-700 font-medium">
                        {message.agentName || '智能体'} · 多步骤分析
                      </span>
                      {message.stepsCompleted !== undefined && message.totalSteps !== undefined && (
                        <span className="text-xs text-blue-500 ml-2">
                          ({message.stepsCompleted}/{message.totalSteps} 步骤)
                        </span>
                      )}
                    </div>
                  )}

                  {/* Schema 验证状态 */}
                  {message.analysisMode && message.validationSummary && (
                    <div className={`mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${
                      message.validationSummary.steps_with_errors > 0
                        ? 'bg-red-50 border border-red-200 text-red-700'
                        : message.validationSummary.steps_with_warnings > 0
                        ? 'bg-yellow-50 border border-yellow-200 text-yellow-700'
                        : 'bg-green-50 border border-green-200 text-green-700'
                    }`}>
                      {message.validationSummary.steps_with_errors > 0 ? (
                        <ShieldAlert className="w-4 h-4" />
                      ) : (
                        <ShieldCheck className="w-4 h-4" />
                      )}
                      <span>
                        {message.validationSummary.steps_with_errors > 0
                          ? `Schema校验: ${message.validationSummary.steps_with_errors}个步骤存在错误，已尝试自动修正`
                          : message.validationSummary.steps_with_warnings > 0
                          ? `Schema校验: ${message.validationSummary.steps_with_warnings}个步骤存在警告`
                          : 'Schema校验: 所有查询已验证'}
                      </span>
                    </div>
                  )}

                  {/* 分析步骤展示 */}
                  {message.analysisMode && message.analysisSteps && message.analysisSteps.length > 0 && (
                    <div className="mt-4 space-y-3">
                      <div className="text-sm font-medium text-gray-700 flex items-center gap-2">
                        <BarChart3 className="w-4 h-4" />
                        分析过程
                      </div>
                      <div className="space-y-2">
                        {message.analysisSteps.map((step, stepIdx) => (
                          <div key={stepIdx} className={`bg-white rounded-lg border p-3 ${
                            step.validation && !step.validation.is_valid
                              ? 'border-red-300 bg-red-50/30'
                              : step.validation && step.validation.warnings.length > 0
                              ? 'border-yellow-300 bg-yellow-50/30'
                              : 'border-gray-200'
                          }`}>
                            <div className="flex items-start gap-2">
                              <div className={`w-5 h-5 rounded-full text-xs flex items-center justify-center flex-shrink-0 mt-0.5 ${
                                step.validation && !step.validation.is_valid
                                  ? 'bg-red-100 text-red-600'
                                  : step.validation && step.validation.warnings.length > 0
                                  ? 'bg-yellow-100 text-yellow-600'
                                  : 'bg-blue-100 text-blue-600'
                              }`}>
                                {stepIdx + 1}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <div className="text-sm font-medium text-gray-800">{step.description}</div>
                                  {step.validation && !step.validation.is_valid && (
                                    <span className="px-1.5 py-0.5 bg-red-100 text-red-600 text-xs rounded">已修正</span>
                                  )}
                                  {step.validation && step.validation.warnings.length > 0 && (
                                    <span className="px-1.5 py-0.5 bg-yellow-100 text-yellow-600 text-xs rounded">警告</span>
                                  )}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">{step.purpose}</div>

                                {/* 验证错误提示 */}
                                {step.validation && step.validation.errors.length > 0 && (
                                  <div className="mt-2 text-xs text-red-600 bg-red-50 rounded p-2">
                                    <div className="font-medium">Schema错误（已自动修正）:</div>
                                    <ul className="mt-1 space-y-0.5">
                                      {step.validation.errors.map((err, i) => (
                                        <li key={i}>• {err}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {/* 验证警告提示 */}
                                {step.validation && step.validation.warnings.length > 0 && (
                                  <div className="mt-2 text-xs text-yellow-700 bg-yellow-50 rounded p-2">
                                    <div className="font-medium">警告:</div>
                                    <ul className="mt-1 space-y-0.5">
                                      {step.validation.warnings.map((warn, i) => (
                                        <li key={i}>• {warn}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}

                                {step.insight && (
                                  <div className="mt-2 text-sm text-gray-600 bg-gray-50 rounded p-2">
                                    <span className="text-blue-600 font-medium">发现：</span>
                                    {step.insight.length > 150 ? step.insight.substring(0, 150) + '...' : step.insight}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 行动建议 */}
                  {message.analysisMode && message.recommendations && message.recommendations.length > 0 && (
                    <div className="mt-4 bg-green-50 rounded-lg border border-green-100 p-4">
                      <div className="text-sm font-medium text-green-800 flex items-center gap-2 mb-2">
                        <Lightbulb className="w-4 h-4" />
                        行动建议
                      </div>
                      <ul className="space-y-2">
                        {message.recommendations.map((rec, recIdx) => (
                          <li key={recIdx} className="text-sm text-green-700 flex items-start gap-2">
                            <span className="text-green-500 font-medium">{recIdx + 1}.</span>
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* 置信度 */}
                  {message.analysisMode && message.confidence !== undefined && (
                    <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            message.confidence >= 0.8 ? 'bg-green-500' :
                            message.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${message.confidence * 100}%` }}
                        />
                      </div>
                      <span>置信度 {Math.round(message.confidence * 100)}%</span>
                    </div>
                  )}

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
