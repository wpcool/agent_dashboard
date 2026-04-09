import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Sparkles, ChevronLeft } from 'lucide-react';

interface Skill {
  id: string;
  code: string;
  name: string;
  description?: string;
  icon: string;
  skill_type: string;
  capabilities: string[];
  system_prompt_fragment?: string;
}

interface SkillManagerProps {
  onBack: () => void;
}

export const SkillManager: React.FC<SkillManagerProps> = ({ onBack }) => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSkills();
  }, []);

  const fetchSkills = async () => {
    try {
      const response = await api.get('/api/v1/skills');
      setSkills(response.data);
      if (response.data.length > 0) {
        setSelectedSkill(response.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch skills:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-1 text-gray-500 hover:text-gray-700"
          >
            <ChevronLeft className="w-5 h-5" />
            返回
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">技能</h1>
            <p className="text-gray-500">管理可复用的指令，让数据智能体在需要时按需激活</p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-400">加载中...</div>
        ) : (
          <div className="flex gap-6">
            {/* Skill List */}
            <div className="w-80 bg-white rounded-xl border border-gray-100 overflow-hidden">
              <div className="p-4 border-b border-gray-100">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-gray-400" />
                  <span className="font-medium text-gray-700">技能</span>
                </div>
              </div>
              <div className="divide-y divide-gray-50">
                {skills.map((skill) => (
                  <button
                    key={skill.id}
                    onClick={() => setSelectedSkill(skill)}
                    className={`w-full text-left p-4 hover:bg-gray-50 transition-colors ${
                      selectedSkill?.id === skill.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-xl">{skill.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-800">{skill.name}</span>
                          {skill.skill_type === 'builtin' && (
                            <span className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
                              内置
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 mt-1 truncate">
                          {skill.description}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Skill Detail */}
            <div className="flex-1 bg-white rounded-xl border border-gray-100 p-6">
              {selectedSkill ? (
                <div>
                  <div className="flex items-center gap-3 mb-6">
                    <span className="text-3xl">{selectedSkill.icon}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-xl font-semibold text-gray-800">{selectedSkill.name}</h2>
                        {selectedSkill.skill_type === 'builtin' && (
                          <span className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
                            内置
                          </span>
                        )}
                      </div>
                      <p className="text-gray-500">{selectedSkill.description}</p>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">能力标签</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedSkill.capabilities?.map((cap) => (
                        <span
                          key={cap}
                          className="px-3 py-1 bg-blue-50 text-blue-600 text-sm rounded-full"
                        >
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-3">系统提示词</h3>
                    {selectedSkill.skill_type === 'builtin' ? (
                      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 whitespace-pre-wrap">
                        {selectedSkill.system_prompt_fragment || '无配置'}
                      </div>
                    ) : (
                      <textarea
                        className="w-full h-64 p-4 border border-gray-200 rounded-lg text-sm font-mono focus:outline-none focus:border-blue-400"
                        value={selectedSkill.system_prompt_fragment || ''}
                        readOnly
                      />
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-400">
                  选择一个技能查看详情
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
