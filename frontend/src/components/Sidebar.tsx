import React, { useState } from 'react';

interface SidebarProps {
  currentView: string;
  onViewChange: (view: string) => void;
  conversations: { id: string; title: string }[];
}

const menuItems = [
  { id: 'chat', label: '对话', icon: '💬' },
  { id: 'canvas', label: '画卷', icon: '🎨' },
  { id: 'dashboard', label: '仪表盘', icon: '📊' },
];

const dataSubMenu = [
  { id: 'data-source', label: '数据源', icon: '🔌' },
  { id: 'roles', label: '角色权限', icon: '👥' },
  { id: 'terms', label: '术语偏好', icon: '📝' },
  { id: 'tunnel', label: '安全隧道', icon: '🔒' },
];

const bottomMenu = [
  { id: 'quick-search', label: '速查', icon: '🔍' },
  { id: 'api-key', label: 'API-Key', icon: '🔑' },
  { id: 'settings', label: '设置', icon: '⚙️' },
  { id: 'docs', label: '文档', icon: '📄' },
  { id: 'contact', label: '联系我们', icon: '💬' },
  { id: 'deploy', label: '私有部署', icon: '🚀' },
];

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onViewChange, conversations }) => {
  const [dataExpanded, setDataExpanded] = useState(true);
  const [projectExpanded, setProjectExpanded] = useState(true);

  return (
    <div className="w-60 h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="p-4 flex items-center gap-2">
        <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">AT</span>
        </div>
        <span className="font-semibold text-gray-800">AskTable</span>
        <button className="ml-auto text-gray-400 hover:text-gray-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>

      {/* Project Selector */}
      <div className="px-4 pb-2">
        <button
          onClick={() => setProjectExpanded(!projectExpanded)}
          className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-gray-100 text-sm"
        >
          <span className="text-gray-700">王小鸟的项目</span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${projectExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Main Menu */}
      <div className="flex-1 overflow-y-auto px-2">
        {/* Primary Menu */}
        <div className="space-y-1 mb-4">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                currentView === item.id
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        {/* Data Section */}
        <div className="mb-4">
          <button
            onClick={() => setDataExpanded(!dataExpanded)}
            className="w-full flex items-center justify-between px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <span>🗄️</span>
              <span>数据</span>
            </div>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform ${dataExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {dataExpanded && (
            <div className="mt-1 ml-4 space-y-1">
              {dataSubMenu.map((item) => (
                <button
                  key={item.id}
                  onClick={() => onViewChange(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentView === item.id
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="text-xs">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Recent Conversations */}
        {conversations.length > 0 && (
          <div className="mb-4">
            <div className="px-3 py-2 text-xs text-gray-400 font-medium">最近对话</div>
            <div className="space-y-1">
              {conversations.slice(0, 5).map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onViewChange(`chat-${conv.id}`)}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 truncate"
                >
                  <span>💬</span>
                  <span className="truncate">{conv.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Bottom Menu */}
        <div className="space-y-1">
          {bottomMenu.map((item) => (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                currentView === item.id
                  ? 'bg-blue-50 text-blue-600'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* User Profile */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-gray-600 text-sm font-medium">
            王
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-gray-700 truncate">王小鸟</div>
            <div className="text-xs text-gray-400">试用</div>
          </div>
          <button className="text-gray-400 hover:text-gray-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
            </svg>
          </button>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <span>🪙</span>
            <span>20 积分</span>
          </div>
          <button className="px-3 py-1 bg-blue-500 text-white text-xs rounded-full hover:bg-blue-600">
            升级
          </button>
        </div>
      </div>
    </div>
  );
};
