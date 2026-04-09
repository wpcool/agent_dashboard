import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Welcome } from './components/Welcome';
import { AgentGrid } from './components/AgentGrid';
import { AgentMarket } from './components/AgentMarket';
import { SkillManager } from './components/SkillManager';
import { DataSourceManager } from './components/DataSource';
import { Chat } from './components/Chat';
import { PlaceholderPage } from './components/PlaceholderPage';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState('chat');
  const [conversations] = useState<{ id: string; title: string }[]>([
    { id: '1', title: '销售数据展示' },
    { id: '2', title: '销售分析' },
  ]);
  const [activeAgent, setActiveAgent] = useState<string | undefined>();
  const [initialMessage, setInitialMessage] = useState<string | undefined>();

  const handleStartChat = (agentId?: string, message?: string) => {
    setActiveAgent(agentId);
    setInitialMessage(message);
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
            initialMessage={initialMessage}
            onBack={() => {
              setCurrentView('chat');
              setInitialMessage(undefined);
            }}
          />
        );
      case 'agents':
        return (
          <AgentMarket
            onSelectAgent={(agentId) => handleStartChat(agentId)}
            onCreateAgent={() => setCurrentView('agent-create')}
            onViewSkills={() => setCurrentView('skills')}
          />
        );
      case 'skills':
        return (
          <SkillManager
            onBack={() => setCurrentView('agents')}
          />
        );
      case 'data-source':
        return <DataSourceManager />;
      case 'dashboard':
        return (
          <PlaceholderPage
            icon="📊"
            title="仪表盘"
            description="一站式数据看板，实时监控关键业务指标"
            features={[
              '自定义数据看板布局',
              '实时数据刷新',
              '红黄绿灯预警指示',
              '一键分享和导出',
            ]}
            actionText="先体验对话功能"
            onAction={() => setCurrentView('chat')}
          />
        );
      case 'canvas':
        return (
          <PlaceholderPage
            icon="🎨"
            title="画卷"
            description="可视化画布，拖拽式数据分析与报告制作"
            features={[
              '拖拽式图表编排',
              '丰富的图表类型',
              '智能数据推荐',
              '多人协作编辑',
            ]}
            actionText="先体验对话功能"
            onAction={() => setCurrentView('chat')}
          />
        );
      case 'roles':
        return (
          <PlaceholderPage
            icon="👥"
            title="角色权限"
            description="精细化数据访问控制，保障数据安全"
            features={[
              '基于角色的权限管理',
              '表级/字段级权限控制',
              '数据脱敏规则配置',
              '操作审计日志',
            ]}
          />
        );
      case 'terms':
        return (
          <PlaceholderPage
            icon="📝"
            title="术语偏好"
            description="统一业务术语，提升AI理解准确度"
            features={[
              '业务术语词典管理',
              '同义词映射配置',
              '指标定义管理',
              'AI理解优化',
            ]}
          />
        );
      case 'tunnel':
        return (
          <PlaceholderPage
            icon="🔒"
            title="安全隧道"
            description="安全连接私有数据库，数据不出域"
            features={[
              'SSL加密传输',
              'IP白名单控制',
              '访问频率限制',
              '连接审计日志',
            ]}
          />
        );
      default:
        return (
          <PlaceholderPage
            icon="🚀"
            title="功能即将上线"
            description="我们正努力开发更多功能"
            features={['敬请期待...']}
            actionText="返回对话"
            onAction={() => setCurrentView('chat')}
          />
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
