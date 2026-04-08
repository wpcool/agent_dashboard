import React from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

type ChartType = 'line' | 'bar' | 'pie';

interface ChartViewProps {
  data: any[];
  columns: string[];
  type?: ChartType;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export const ChartView: React.FC<ChartViewProps> = ({ data, columns, type = 'bar' }) => {
  if (!data || data.length === 0) return null;

  // 自动检测图表类型
  const numericColumns = columns.filter(col =>
    typeof data[0][col] === 'number' || !isNaN(Number(data[0][col]))
  );
  const stringColumns = columns.filter(col =>
    typeof data[0][col] === 'string' || isNaN(Number(data[0][col]))
  );

  // 转换数据格式
  const chartData = data.map(row => {
    const newRow: any = {};
    columns.forEach(col => {
      const val = row[col];
      newRow[col] = typeof val === 'number' ? val : Number(val) || val;
    });
    return newRow;
  });

  if (type === 'pie' && numericColumns.length >= 1 && stringColumns.length >= 1) {
    // 饼图：第一个字符串列作为名称，第一个数字列作为值
    const nameKey = stringColumns[0];
    const valueKey = numericColumns[0];
    const pieData = chartData.map(item => ({
      name: item[nameKey],
      value: Number(item[valueKey]) || 0
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {pieData.map((_entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (type === 'line' && numericColumns.length >= 1) {
    // 折线图
    const xKey = stringColumns[0] || numericColumns[0];
    const yKey = numericColumns[numericColumns[0] === xKey ? 1 : 0] || numericColumns[0];

    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke="#3b82f6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  // 默认柱状图
  const xKey = stringColumns[0] || columns[0];
  const yKeys = numericColumns.length > 0 ? numericColumns : [columns[1] || columns[0]].filter(Boolean);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {yKeys.map((key, idx) => (
          <Bar key={key} dataKey={key} fill={COLORS[idx % COLORS.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

export default ChartView;
