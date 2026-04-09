import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Plus, Sparkles, ChevronRight } from 'lucide-react';

interface Skill {
  id: string;
  code: string;
  name: string;
  description?: string;
  icon: string;
}

interface Agent {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_builtin: boolean;
  skills: Skill[];
}

interface AgentMarketProps {
  onSelectAgent: (agentId: string) => void;
  onCreateAgent: () => void;
  onViewSkills: () => void;
}

export const AgentMarket: React.FC<AgentMarketProps> = ({
  onSelectAgent,
  onCreateAgent,
  onViewSkills,
}) => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await api.get('/api/v1/agents');
      setAgents(response.data);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const builtinAgents = agents.filter(a => a.is_builtin);
  const customAgents = agents.filter(a => !a.is_builtin);

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">数据智能体</h1>
          <p className="text-gray-500">创建和管理数据智能体，用 AI 查询您的数据源</p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={onCreateAgent}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            创建智能体
          </button>
          <button
            onClick={onViewSkills}
            className="flex items-center gap-2 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            管理技能
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">加载中...</div>
        ) : (
          <>
            {/* Built-in Agents */}
            <div className="mb-10">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">内置智能体</h2>
              <div className="grid grid-cols-3 gap-4">
                {builtinAgents.map((agent) => (
                  <div
                    key={agent.id}
                    onClick={() => onSelectAgent(agent.id)}
                    className="bg-white rounded-xl p-5 border border-gray-100 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center text-2xl">
                        🤖
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-800 truncate">{agent.name}</h3>
                          <span className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">内置</span>
                        </div>
                        <p className="text-xs text-gray-400 mt-1">{agent.skills.length} 个技能</p>
                      </div>
                    </div>
                    <p className="text-sm text-gray-500 line-clamp-2">{agent.description}</p>
                    <div className="flex flex-wrap gap-1 mt-3">
                      {agent.skills.slice(0, 3).map((skill) => (
                        <span
                          key={skill.id}
                          className="px-2 py-0.5 bg-gray-50 text-gray-500 text-xs rounded"
                        >
                          {skill.name}
                        </span>
                      ))}
                      {agent.skills.length > 3 && (
                        <span className="px-2 py-0.5 bg-gray-50 text-gray-400 text-xs rounded">
                          +{agent.skills.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Custom Agents */}
            {customAgents.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-800 mb-4">我的智能体</h2>
                <div className="grid grid-cols-3 gap-4">
                  {customAgents.map((agent) => (
                    <div
                      key={agent.id}
                      onClick={() => onSelectAgent(agent.id)}
                      className="bg-white rounded-xl p-5 border border-gray-100 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                    >
                      <div className="flex items-start gap-3 mb-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-green-100 to-blue-100 rounded-xl flex items-center justify-center text-2xl">
                          🤖
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-800 truncate">{agent.name}</h3>
                          <p className="text-xs text-gray-400 mt-1">{agent.skills.length} 个技能</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 line-clamp-2">{agent.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};
