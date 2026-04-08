import React, { useState, useEffect } from 'react';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { chatApi } from '../api/chat';
import { Message, ChatResponse } from '../types/chat';

export const ChatWindow: React.FC = () => {
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentResults, setCurrentResults] = useState<Record<string, unknown>[] | undefined>();
  const [loading, setLoading] = useState(false);

  // 创建新对话
  useEffect(() => {
    const initConversation = async () => {
      try {
        const { data } = await chatApi.createConversation();
        setConversationId(data.id);
      } catch (error) {
        console.error('Failed to create conversation:', error);
      }
    };
    initConversation();
  }, []);

  const handleSendMessage = async (content: string) => {
    if (!conversationId) return;

    // 添加用户消息到列表
    const userMessage: Message = {
      id: Date.now().toString(),
      conversation_id: conversationId,
      role: 'user',
      content,
      content_type: 'text',
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setCurrentResults(undefined);

    try {
      const { data } = await chatApi.sendMessage({
        message: content,
        conversation_id: conversationId,
      });

      // 添加助手消息
      setMessages((prev) => [...prev, data.message]);

      // 如果有结果，保存
      if (data.results) {
        setCurrentResults(data.results);
      }

      // 如果需要验证，显示提示
      if (data.needs_verification) {
        console.log('Needs verification:', data.explanation);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // 显示错误消息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        conversation_id: conversationId,
        role: 'assistant',
        content: '抱歉，处理你的请求时出现了错误。请稍后重试。',
        content_type: 'text',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 头部 */}
      <header className="bg-white border-b px-4 py-3">
        <h1 className="text-lg font-semibold text-gray-800">AskTable AI</h1>
        <p className="text-sm text-gray-500">智能数据分析助手</p>
      </header>

      {/* 消息列表 */}
      <MessageList
        messages={messages}
        results={currentResults}
        loading={loading}
      />

      {/* 输入框 */}
      <ChatInput onSend={handleSendMessage} loading={loading} />
    </div>
  );
};
