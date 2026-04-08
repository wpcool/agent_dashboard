import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Welcome } from './components/Welcome';
import { AgentGrid } from './components/AgentGrid';
import { DataSourceManager } from './components/DataSource';
import { Chat } from './components/Chat';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState('chat');
  const [conversations] = useState<{ id: string; title: string }[]>([
    { id: '1', title: '销售数据展示' },
    { id: '2', title: '销售分析' },
  ]);
  const [activeAgent, setActiveAgent] = useState<string | undefined>();

  const handleStartChat = (agentId?: string) => {
    setActiveAgent(agentId);
    setCurrentView('chat-active');
  };

  const handleViewAgents = () => {
    setCurrentView('agents');
  };

  const renderMainContent = () => {
    switch (currentView) {
      case 'chat':
        return (
          <Welcome
            onStartChat={handleStartChat}
            onViewAgents={handleViewAgents}
          />
        );
      case 'chat-active':
        return (
          <Chat
            agentId={activeAgent}
            onBack={() => setCurrentView('chat')}
          />
        );
      case 'agents':
        return (
          <AgentGrid
            onSelectAgent={(agentId) => handleStartChat(agentId)}
          />
        );
      case 'data-source':
        return <DataSourceManager />;
      case 'dashboard':
        return (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-6xl mb-4">📊</div>
              <p>仪表盘功能开发中...</p>
            </div>
          </div>
        );
      case 'canvas':
        return (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-6xl mb-4">🎨</div>
              <p>画卷功能开发中...</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="flex-1 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <div className="text-6xl mb-4">🚧</div>
              <p>功能开发中...</p>
            </div>
          </div>
        );
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        currentView={currentView}
        onViewChange={setCurrentView}
        conversations={conversations}
      />
      {renderMainContent()}
    </div>
  );
};

export default App;
