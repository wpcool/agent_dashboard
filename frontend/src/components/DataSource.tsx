import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { FileUploader } from './FileUploader';
import { Trash2, MessageSquare, MoreVertical } from 'lucide-react';

interface DataSourceManagerProps {
  onBack?: () => void;
}

interface DataSourceItem {
  id: string;
  name: string;
  type: string;
  description: string;
  tables: number;
  columns: number;
  updatedAt: string;
  status: 'connected' | 'error' | 'syncing';
  schema_cache?: any;
}


const fileSources = [
  { id: 'excel', name: 'Excel / CSV', icon: '📊', extensions: '.xlsx / .xls / .csv' },
  { id: 'feishu', name: '飞书多维表格', icon: '📋', extensions: 'Bitable' },
];

const dbSources = [
  { id: 'mysql', name: 'MySQL', icon: '🐬', version: '5.7 / 8.0' },
  { id: 'postgresql', name: 'PostgreSQL', icon: '🐘', version: '9/14/15/16' },
  { id: 'polardb-mysql', name: 'PolarDB', icon: '❄️', version: 'MySQL 5.7 / 8.0' },
  { id: 'polardb-pg', name: 'PolarDB', icon: '❄️', version: 'PostgreSQL 14/15/16' },
  { id: 'oceanbase', name: 'OceanBase', icon: '🌊', version: '4.2.2' },
  { id: 'dameng', name: '达梦', icon: '🔷', version: 'DM8' },
  { id: 'tidb', name: 'TiDB', icon: '⚡', version: '7.x / 8.x' },
  { id: 'oracle', name: 'Oracle', icon: '🏛️', version: '19c' },
  { id: 'gaussdb', name: 'GaussDB', icon: '🔶', version: 'opengauss 5.x' },
];

export const DataSourceManager: React.FC<DataSourceManagerProps> = ({ onBack: _onBack }) => {
  const [view, setView] = useState<'list' | 'add' | 'config' | 'upload'>('list');
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [dataSources, setDataSources] = useState<DataSourceItem[]>([]);
  const [loading, setLoading] = useState(false);

  // 加载数据源列表
  useEffect(() => {
    if (view === 'list') {
      fetchDataSources();
    }
  }, [view]);

  const fetchDataSources = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/v1/data-sources');
      // 转换后端数据格式
      const formatted = response.data.map((ds: any) => ({
        id: ds.id,
        name: ds.name,
        type: ds.type,
        description: ds.name === '示例销售数据'
          ? '包含商品、订单、客户等销售演示数据'
          : '自定义数据源',
        tables: ds.schema_cache?.tables?.length || 0,
        columns: ds.schema_cache?.tables?.reduce((acc: number, t: any) => acc + (t.columns?.length || 0), 0) || 0,
        updatedAt: ds.schema_cache_updated_at
          ? new Date(ds.schema_cache_updated_at).toLocaleString('zh-CN')
          : '刚刚',
        status: 'connected' as const,
        schema_cache: ds.schema_cache,
      }));
      setDataSources(formatted);
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
    } finally {
      setLoading(false);
    }
  };

  const [config, setConfig] = useState({
    host: '',
    port: '',
    database: '',
    username: '',
    password: '',
  });

  // 删除相关状态
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // 删除数据源
  const handleDelete = async (sourceId: string) => {
    setDeletingId(sourceId);
    try {
      await api.delete(`/api/v1/data-sources/${sourceId}`);
      // 刷新列表
      await fetchDataSources();
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete data source:', error);
      alert('删除失败，请重试');
    } finally {
      setDeletingId(null);
    }
  };

  if (view === 'add') {
    return (
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          {/* Steps */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">1</div>
                <span className="text-blue-600 font-medium">选择类型</span>
              </div>
              <div className="w-16 h-px bg-gray-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">2</div>
                <span className="text-gray-400">配置连接</span>
              </div>
              <div className="w-16 h-px bg-gray-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">3</div>
                <span className="text-gray-400">添加数据表</span>
              </div>
            </div>
          </div>

          {/* File Sources */}
          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center gap-2">
              <span>📄</span> 文件
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {fileSources.map((source) => (
                <button
                  key={source.id}
                  onClick={() => {
                    if (source.id === 'excel') {
                      setView('upload');
                    } else {
                      setSelectedType(source.id);
                    }
                  }}
                  className={`p-6 rounded-xl border-2 text-center transition-all ${
                    selectedType === source.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className="text-4xl mb-3">{source.icon}</div>
                  <div className="font-medium text-gray-800">{source.name}</div>
                  <div className="text-sm text-gray-400">{source.extensions}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Database Sources */}
          <div>
            <h3 className="text-lg font-medium text-gray-800 mb-4 flex items-center gap-2">
              <span>🗄️</span> 数据库
            </h3>
            <div className="grid grid-cols-3 gap-4">
              {dbSources.map((source) => (
                <button
                  key={source.id}
                  onClick={() => {
                    setSelectedType(source.id);
                    setView('config');
                  }}
                  className={`p-6 rounded-xl border-2 text-center transition-all ${
                    selectedType === source.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                >
                  <div className="text-4xl mb-3">{source.icon}</div>
                  <div className="font-medium text-gray-800">{source.name}</div>
                  <div className="text-sm text-gray-400">{source.version}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Back Button */}
          <div className="mt-8 flex justify-between">
            <button
              onClick={() => setView('list')}
              className="px-6 py-2 text-gray-600 hover:text-gray-800"
            >
              ← 返回
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'config') {
    return (
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto">
          {/* Steps */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">✓</div>
                <span className="text-green-600 font-medium">选择类型</span>
              </div>
              <div className="w-16 h-px bg-blue-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">2</div>
                <span className="text-blue-600 font-medium">配置连接</span>
              </div>
              <div className="w-16 h-px bg-gray-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">3</div>
                <span className="text-gray-400">添加数据表</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold text-gray-800 mb-6">配置数据库连接</h2>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">主机地址</label>
                  <input
                    type="text"
                    placeholder="localhost"
                    value={config.host}
                    onChange={(e) => setConfig({ ...config, host: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">端口</label>
                  <input
                    type="text"
                    placeholder="3306"
                    value={config.port}
                    onChange={(e) => setConfig({ ...config, port: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">数据库名称</label>
                <input
                  type="text"
                  placeholder="my_database"
                  value={config.database}
                  onChange={(e) => setConfig({ ...config, database: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">用户名</label>
                <input
                  type="text"
                  placeholder="root"
                  value={config.username}
                  onChange={(e) => setConfig({ ...config, username: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">密码</label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={config.password}
                  onChange={(e) => setConfig({ ...config, password: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400"
                />
              </div>
            </div>

            <div className="flex gap-4 mt-8">
              <button
                onClick={() => setView('add')}
                className="flex-1 px-6 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
              >
                上一步
              </button>
              <button
                onClick={() => {
                  // 模拟连接测试
                  alert('连接成功！');
                  setView('list');
                }}
                className="flex-1 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                测试连接
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Upload view
  if (view === 'upload') {
    return (
      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-4xl mx-auto">
          {/* Steps */}
          <div className="flex items-center justify-center mb-8">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-medium">✓</div>
                <span className="text-green-600 font-medium">选择类型</span>
              </div>
              <div className="w-16 h-px bg-blue-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium">2</div>
                <span className="text-blue-600 font-medium">上传文件</span>
              </div>
              <div className="w-16 h-px bg-gray-200" />
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gray-200 text-gray-500 rounded-full flex items-center justify-center text-sm font-medium">3</div>
                <span className="text-gray-400">完成</span>
              </div>
            </div>
          </div>

          <FileUploader
            onUploadSuccess={() => {
              fetchDataSources();
              setTimeout(() => {
                setView('list');
              }, 1500);
            }}
            onCancel={() => setView('add')}
          />

          <div className="mt-8 flex justify-center">
            <button
              onClick={() => setView('add')}
              className="px-6 py-2 text-gray-600 hover:text-gray-800 transition-colors"
            >
              ← 返回选择类型
            </button>
          </div>
        </div>
      </div>
    );
  }

  // List view
  return (
    <div className="flex-1 overflow-y-auto p-8">
      {/* 删除确认对话框 */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">确认删除</h3>
            <p className="text-gray-600 mb-6">
              确定要删除数据源"{dataSources.find(s => s.id === showDeleteConfirm)?.name}"吗？此操作不可恢复。
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50"
                disabled={deletingId === showDeleteConfirm}
              >
                取消
              </button>
              <button
                onClick={() => handleDelete(showDeleteConfirm)}
                disabled={deletingId === showDeleteConfirm}
                className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {deletingId === showDeleteConfirm ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    删除中...
                  </>
                ) : (
                  '确认删除'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">数据</h1>
            <p className="text-gray-500 mt-1">在这里查看和管理您的数据</p>
          </div>
          <button
            onClick={() => setView('add')}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
          >
            <span>+</span>
            添加数据
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-400">加载中...</div>
          </div>
        ) : dataSources.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center border border-gray-100">
            <div className="text-6xl mb-4">🗄️</div>
            <h3 className="text-lg font-medium text-gray-800 mb-2">还没有数据源</h3>
            <p className="text-gray-500 mb-6">添加您的第一个数据源，开始AI数据分析之旅</p>
            <button
              onClick={() => setView('add')}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              添加数据源
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {dataSources.map((source) => (
              <div
                key={source.id}
                className="bg-white rounded-xl p-6 border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center text-2xl">
                    📊
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-800">{source.name}</h3>
                      <span className="px-2 py-0.5 bg-green-100 text-green-600 text-xs rounded-full flex items-center gap-1">
                        <span>✓</span> 已连接
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-2">{source.description}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>ID: ds_{source.id}</span>
                      <button className="text-gray-400 hover:text-gray-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                    <div className="flex items-center justify-between mt-3 text-sm text-gray-400">
                      <span>表/列数量:{source.tables}/{source.columns}</span>
                      <span>更新于{source.updatedAt}</span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      onClick={() => setShowDeleteConfirm(source.id)}
                      title="删除数据源"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
