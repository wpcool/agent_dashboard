import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileSpreadsheet, FileText, X, Check, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';

interface FileUploaderProps {
  onUploadSuccess: (data: any) => void;
  onCancel: () => void;
}

interface UploadState {
  file: File | null;
  preview: any[];
  columns: any[];
  uploading: boolean;
  progress: number;
  error: string | null;
  success: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess, onCancel }) => {
  const [state, setState] = useState<UploadState>({
    file: null,
    preview: [],
    columns: [],
    uploading: false,
    progress: 0,
    error: null,
    success: false,
  });
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dataSourceName, setDataSourceName] = useState('');

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const validateFile = (file: File): string | null => {
    const allowedTypes = ['.xlsx', '.xls', '.csv'];
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedTypes.includes(ext)) {
      return `不支持的文件格式。仅支持: ${allowedTypes.join(', ')}`;
    }
    if (file.size > 50 * 1024 * 1024) {
      return '文件大小不能超过 50MB';
    }
    return null;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const error = validateFile(file);
      if (error) {
        setState(prev => ({ ...prev, error }));
      } else {
        setState(prev => ({ ...prev, file, error: null }));
        if (!dataSourceName) {
          setDataSourceName(file.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  }, [dataSourceName]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const error = validateFile(file);
      if (error) {
        setState(prev => ({ ...prev, error }));
      } else {
        setState(prev => ({ ...prev, file, error: null }));
        if (!dataSourceName) {
          setDataSourceName(file.name.replace(/\.[^/.]+$/, ''));
        }
      }
    }
  };

  const handleUpload = async () => {
    if (!state.file) return;

    setState(prev => ({ ...prev, uploading: true, error: null }));

    const formData = new FormData();
    formData.append('file', state.file);
    if (dataSourceName) {
      formData.append('name', dataSourceName);
    }

    try {
      const response = await api.post('/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setState(prev => ({ ...prev, progress }));
          }
        },
      });

      setState(prev => ({
        ...prev,
        uploading: false,
        success: true,
        preview: response.data.preview || [],
        columns: response.data.columns || [],
      }));

      onUploadSuccess(response.data);
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        uploading: false,
        error: error.response?.data?.detail || '上传失败，请重试',
      }));
    }
  };

  const getFileIcon = (filename: string) => {
    const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase();
    if (['.xlsx', '.xls'].includes(ext)) {
      return <FileSpreadsheet className="w-12 h-12 text-green-500" />;
    }
    return <FileText className="w-12 h-12 text-blue-500" />;
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* 标题 */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">上传数据文件</h2>
        <p className="text-gray-500">支持 Excel (.xlsx, .xls) 和 CSV 格式，最大 50MB</p>
      </div>

      {/* 上传区域 */}
      {!state.file ? (
        <div
          className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-colors cursor-pointer ${
            dragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400 bg-gray-50'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".xlsx,.xls,.csv"
            onChange={handleChange}
          />
          <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-lg text-gray-600 mb-2">
            <span className="text-blue-500 font-medium">点击上传</span> 或拖拽文件到此处
          </p>
          <p className="text-sm text-gray-400">支持 .xlsx, .xls, .csv</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          {/* 文件信息 */}
          <div className="flex items-start gap-4 mb-6">
            {getFileIcon(state.file.name)}
            <div className="flex-1">
              <h3 className="font-medium text-gray-800">{state.file.name}</h3>
              <p className="text-sm text-gray-500">
                {(state.file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            {!state.uploading && !state.success && (
              <button
                onClick={() => {
                  setState(prev => ({ ...prev, file: null, error: null }));
                  setDataSourceName('');
                }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* 数据源名称 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              数据源名称
            </label>
            <input
              type="text"
              value={dataSourceName}
              onChange={(e) => setDataSourceName(e.target.value)}
              placeholder="输入数据源名称"
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-500"
              disabled={state.uploading || state.success}
            />
          </div>

          {/* 错误提示 */}
          {state.error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 text-red-600 rounded-lg mb-4">
              <AlertCircle className="w-5 h-5" />
              <span>{state.error}</span>
            </div>
          )}

          {/* 上传进度 */}
          {state.uploading && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">上传中...</span>
                <span className="text-sm text-blue-600 font-medium">{state.progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${state.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* 成功提示 */}
          {state.success && (
            <div className="flex items-center gap-2 p-4 bg-green-50 text-green-600 rounded-lg mb-4">
              <Check className="w-5 h-5" />
              <span>上传成功！已创建数据源</span>
            </div>
          )}

          {/* 数据预览 */}
          {state.preview.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-3">数据预览（前5行）</h4>
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      {state.columns.map((col: any) => (
                        <th key={col.name} className="px-3 py-2 text-left font-medium text-gray-600 border-b">
                          <div>{col.name}</div>
                          <div className="text-xs text-gray-400 font-normal">
                            {col.original_name !== col.name ? `原: ${col.original_name}` : ''}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {state.preview.map((row, idx) => (
                      <tr key={idx} className="border-b last:border-0">
                        {state.columns.map((col: any) => (
                          <td key={col.name} className="px-3 py-2 text-gray-600">
                            {row[col.name]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                共 {state.columns.length} 列，已清理列名以符合 SQL 规范
              </p>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-3">
            <button
              onClick={onCancel}
              className="flex-1 px-4 py-2 border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {state.success ? '完成' : '取消'}
            </button>
            {!state.success && (
              <button
                onClick={handleUpload}
                disabled={state.uploading}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                {state.uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    上传中...
                  </>
                ) : (
                  '开始上传'
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUploader;
