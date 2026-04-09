import React, { useState, useEffect } from 'react';
import {
  MessageSquare, Palette, LayoutDashboard, Database, ChevronDown,
  Users, FileText, Lock, Search, Key, Settings, HelpCircle,
  Rocket, MoreVertical, Sparkles, Plus
} from 'lucide-react';
import { api } from '../api/client';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  conversations: { id: string; title: string }[];
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
}

const menuItems = [
  { id: 'chat', label: '对话', icon: MessageSquare },
  { id: 'agents', label: '数据智能体', icon: Sparkles },
  { id: 'canvas', label: '画卷', icon: Palette },
  { id: 'dashboard', label: '仪表盘', icon: LayoutDashboard },
];

const dataSubMenu = [
  { id: 'data-source', label: '数据源', icon: Database },
  { id: 'roles', label: '角色权限', icon: Users },
  { id: 'terms', label: '术语偏好', icon: FileText },
  { id: 'tunnel', label: '安全隧道', icon: Lock },
];

const bottomMenu = [
  { id: 'quick-search', label: '速查', icon: Search },
  { id: 'api-key', label: 'API-Key', icon: Key },
  { id: 'settings', label: '设置', icon: Settings },
  { id: 'docs', label: '文档', icon: HelpCircle },
  { id: 'deploy', label: '私有部署', icon: Rocket },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange }) => {
  const [dataExpanded, setDataExpanded] = useState(true);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载对话列表
  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/conversations?limit=10');
      setConversations(response.data);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-60 h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-4 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold text-gray-800 text-lg">AskTable</span>
      </div>

      {/* New Chat Button */}
      <div className="px-4 mb-4">
        <button
          onClick={() => onViewChange('chat')}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors font-medium"
        >
          <Plus className="w-4 h-4" />
          新建对话
        </button>
      </div>

      {/* Main Menu */}
      <div className="flex-1 overflow-y-auto px-3">
        {/* Primary Menu */}
        <div className="space-y-1 mb-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                  currentView === item.id
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Data Section */}
        <div className="mb-4">
          <button
            onClick={() => setDataExpanded(!dataExpanded)}
            className="w-full flex items-center justify-between px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <div className="flex items-center gap-3">
              <Database className="w-4 h-4" />
              <span>数据</span>
            </div>
            <ChevronDown
              className={`w-4 h-4 text-gray-400 transition-transform ${dataExpanded ? 'rotate-180' : ''}`}
            />
          </button>

          {dataExpanded && (
            <div className="mt-1 ml-4 space-y-1">
              {dataSubMenu.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => onViewChange(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm transition-colors ${
                      currentView === item.id
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        <div className="mb-4">
          <div className="px-3 py-2 text-xs text-gray-400 font-medium uppercase tracking-wider">
            最近对话
          </div>
          <div className="space-y-1">
            {loading ? (
              <div className="px-3 py-2 text-sm text-gray-400">加载中...</div>
            ) : conversations.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-400">暂无对话</div>
            ) : (
              conversations.slice(0, 5).map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onViewChange(`chat-${conv.id}`)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-gray-600 hover:bg-gray-100 transition-colors text-left"
                >
                  <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <span className="truncate">{conv.title}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Bottom Menu */}
        <div className="space-y-1 pt-4 border-t border-gray-100">
          {bottomMenu.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors ${
                  currentView === item.id
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-gray-200 to-gray-300 rounded-full flex items-center justify-center text-gray-600 text-sm font-bold">
            王
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold text-gray-800 truncate">王小鸟</div>
            <div className="text-xs text-gray-400">试用版</div>
          </div>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
