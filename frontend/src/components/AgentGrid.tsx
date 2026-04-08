import React from 'react';

interface AgentGridProps {
  onSelectAgent: (agentId: string) => void;
}

const agents = [
  {
    id: 'store_analyst',
    name: '门店经营分析师',
    avatar: '👨‍💼',
    tag: '内置',
    description: '专注零售门店经营数据分析，帮你发现门店运营中的机会与问题',
  },
  {
    id: 'ecommerce_monitor',
    name: '电商数据盯盘助手',
    avatar: '📦',
    tag: '内置',
    description: '实时监控电商核心数据，第一时间发现异常和机会',
  },
  {
    id: 'finance_analyst',
    name: '财务数据分析师',
    avatar: '💰',
    tag: '内置',
    description: '深入分析财务数据，帮助把握经营状况，识别财务风险',
  },
  {
    id: 'market_insight',
    name: '市场洞察分析师',
    avatar: '📈',
    tag: '内置',
    description: '追踪市场动态，分析竞争格局，识别市场机会',
  },
  {
    id: 'supply_chain',
    name: '供应链监控官',
    avatar: '🚚',
    tag: '内置',
    description: '实时监控供应链各环节，及时发现风险和优化机会',
  },
  {
    id: 'growth_analyst',
    name: '用户增长分析师',
    avatar: '🚀',
    tag: '内置',
    description: '追踪用户增长指标，分析增长策略效果，识别增长机会',
  },
  {
    id: 'executive_assistant',
    name: '高管数据助手',
    avatar: '👔',
    tag: '内置',
    description: '为高管提供一键式经营数据汇总，辅助快速决策',
  },
  {
    id: 'alert_analyst',
    name: '经营红黄灯分析师',
    avatar: '🚦',
    tag: '内置',
    description: '为各业务线设置红黄灯预警规则，自动追踪指标健康度',
  },
  {
    id: 'data_quality',
    name: '数据质量守护者',
    avatar: '🔍',
    tag: '内置',
    description: '主动监控数据质量，确保分析结果的准确性和可信度',
  },
];

export const AgentGrid: React.FC<AgentGridProps> = ({ onSelectAgent }) => {
  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-3 gap-6">
          {agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => onSelectAgent(agent.id)}
              className="bg-white rounded-xl p-6 border border-gray-100 hover:border-blue-300 hover:shadow-lg transition-all text-left group"
            >
              <div className="flex items-start gap-4 mb-4">
                <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center text-3xl group-hover:scale-110 transition-transform">
                  {agent.avatar}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-800 text-lg">{agent.name}</h3>
                    <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded-full">
                      {agent.tag}
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-gray-500 text-sm leading-relaxed">{agent.description}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
