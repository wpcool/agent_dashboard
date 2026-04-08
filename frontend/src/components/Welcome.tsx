import React, { useState } from 'react';

interface WelcomeProps {
  onStartChat: (agentId?: string) => void;
  onViewAgents: () => void;
}

const features = [
  {
    icon: '🛡️',
    title: '数据安全，注重隐私',
    description: '你的数据，你的规则，隐私至上',
  },
  {
    icon: '🧠',
    title: '记住你的使用习惯',
    description: '学习你的上下文，越用越精准',
  },
  {
    icon: '⚡',
    title: '24小时随时待命',
    description: '飞书、企业微信、钉钉、Slack、Teams、Telegram 多平台接入',
  },
  {
    icon: '📊',
    title: '多种形态',
    description: '分析、报告、看板、大屏，全面为您服务',
  },
];

const quickActions = [
  { icon: '🔍', label: '归因分析' },
  { icon: '📄', label: '生成报告' },
  { icon: '⚡', label: '沉淀业务Skill' },
  { icon: '📥', label: '提取数据' },
  { icon: '🔗', label: '分享结果' },
  { icon: '📊', label: '创建仪表盘' },
  { icon: '📈', label: '决策分析' },
];

const suggestedAgents = [
  {
    id: 'store_analyst',
    name: '门店经营分析师',
    avatar: '👨‍💼',
    description: '专注零售门店经营数据分析，帮你发现门店运营中的机会与问题',
  },
  {
    id: 'ecommerce_monitor',
    name: '电商数据盯盘助手',
    avatar: '📦',
    description: '实时监控电商核心数据，第一时间发现异常和机会',
  },
  {
    id: 'finance_analyst',
    name: '财务数据分析师',
    avatar: '💰',
    description: '深入分析财务数据，帮助把握经营状况，识别财务风险',
  },
];

export const Welcome: React.FC<WelcomeProps> = ({ onStartChat, onViewAgents }) => {
  const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
  const [isRecording, setIsRecording] = useState(false);

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-800 mb-3">
            您的第一位AI数据分析员工
          </h1>
          <p className="text-gray-500">
            用自然语言和我对话，我可以帮你分析数据、发现洞察、生成报告
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-4 gap-4 mb-10">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="text-3xl mb-3">{feature.icon}</div>
              <h3 className="font-semibold text-gray-800 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-500">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="flex flex-wrap justify-center gap-3 mb-10">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={() => onStartChat()}
              className="flex items-center gap-2 px-4 py-2 bg-white rounded-full border border-gray-200 text-sm text-gray-600 hover:border-blue-400 hover:text-blue-600 transition-colors"
            >
              <span>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          ))}
        </div>

        {/* Voice/Text Input */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 mb-10">
          {inputMode === 'voice' ? (
            <div className="text-center">
              <p className="text-gray-500 mb-6">按住空格，语音输入</p>
              <button
                onMouseDown={() => setIsRecording(true)}
                onMouseUp={() => setIsRecording(false)}
                onMouseLeave={() => setIsRecording(false)}
                className="relative w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors"
              >
                {isRecording && (
                  <>
                    <span className="absolute w-full h-full bg-blue-400 rounded-full voice-ripple" />
                    <span className="absolute w-full h-full bg-blue-300 rounded-full voice-ripple delay-100" />
                  </>
                )}
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </button>
              <button
                onClick={() => setInputMode('text')}
                className="mt-6 flex items-center gap-2 mx-auto text-gray-400 hover:text-gray-600 text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                切换到键盘输入
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-4">
              <input
                type="text"
                placeholder="输入你的问题..."
                className="flex-1 px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-blue-400"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    onStartChat();
                  }
                }}
              />
              <button
                onClick={() => onStartChat()}
                className="px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
              >
                发送
              </button>
              <button
                onClick={() => setInputMode('voice')}
                className="p-3 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          )}
        </div>

        {/* Suggested Agents */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-500">
              选择一个智能体开始对话，或直接提问
            </p>
            <button
              onClick={onViewAgents}
              className="flex items-center gap-1 text-blue-500 hover:text-blue-600 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              换一批
            </button>
          </div>
          <div className="grid grid-cols-3 gap-4">
            {suggestedAgents.map((agent) => (
              <button
                key={agent.id}
                onClick={() => onStartChat(agent.id)}
                className="bg-white rounded-xl p-5 border border-gray-100 hover:border-blue-300 hover:shadow-md transition-all text-left"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center text-2xl">
                    {agent.avatar}
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-800">{agent.name}</h4>
                  </div>
                </div>
                <p className="text-sm text-gray-500">{agent.description}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
