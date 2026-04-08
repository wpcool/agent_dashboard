"""
文件处理服务：解析 Excel/CSV 并导入数据库
"""
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime


def infer_sql_type(dtype: str) -> str:
    """根据 pandas 类型推断 SQL 类型"""
    if 'int' in str(dtype).lower():
        return 'INTEGER'
    elif 'float' in str(dtype).lower():
        return 'REAL'
    elif 'datetime' in str(dtype).lower():
        return 'TIMESTAMP'
    elif 'bool' in str(dtype).lower():
        return 'BOOLEAN'
    else:
        return 'TEXT'


def sanitize_column_name(name: str) -> str:
    """清理列名，确保符合 SQL 规范"""
    # 替换特殊字符
    name = name.strip().replace(' ', '_').replace('-', '_')
    # 移除非法字符
    import re
    name = re.sub(r'[^\w]', '', name)
    # 确保不以数字开头
    if name[0].isdigit():
        name = 'col_' + name
    return name.lower() or 'column'


def process_file(
    file_path: str,
    table_name: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理上传的文件并导入 SQLite

    Args:
        file_path: 上传文件的路径
        table_name: 目标表名（可选，默认从文件名生成）
        db_path: 目标数据库路径（可选，默认创建新数据库）

    Returns:
        处理结果信息
    """
    path = Path(file_path)

    # 生成表名
    if not table_name:
        table_name = sanitize_column_name(path.stem)

    # 生成数据库路径
    if not db_path:
        upload_dir = path.parent / 'uploads'
        upload_dir.mkdir(exist_ok=True)
        db_path = str(upload_dir / f'{uuid.uuid4().hex}.db')

    try:
        # 读取文件
        if path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif path.suffix.lower() == '.csv':
            # 尝试检测编码
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='gbk')
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        # 基本信息
        row_count = len(df)
        column_count = len(df.columns)

        # 清理列名
        original_columns = list(df.columns)
        column_mapping = {}
        for col in df.columns:
            new_col = sanitize_column_name(col)
            # 处理重复列名
            counter = 1
            base_name = new_col
            while new_col in column_mapping.values():
                new_col = f"{base_name}_{counter}"
                counter += 1
            column_mapping[col] = new_col

        df = df.rename(columns=column_mapping)

        # 推断列类型
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            sql_type = infer_sql_type(dtype)
            columns_info.append({
                'name': col,
                'original_name': [k for k, v in column_mapping.items() if v == col][0],
                'type': sql_type,
                'pandas_type': dtype
            })

        # 创建 SQLite 连接
        conn = sqlite3.connect(db_path)

        # 处理数据类型问题（特别是 datetime）
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)

        # 处理 NaN 值
        df = df.where(pd.notnull(df), None)

        # 导入数据
        df.to_sql(table_name, conn, index=False, if_exists='replace')

        conn.close()

        # 生成 Schema
        schema = {
            "tables": [
                {
                    "name": table_name,
                    "columns": [
                        {
                            "name": col['name'],
                            "type": col['type'],
                            "nullable": True
                        }
                        for col in columns_info
                    ],
                    "primary_key": ["rowid"]
                }
            ]
        }

        return {
            "success": True,
            "table_name": table_name,
            "db_path": db_path,
            "row_count": row_count,
            "column_count": column_count,
            "columns": columns_info,
            "schema": schema,
            "preview": df.head(5).to_dict('records')
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_table_preview(db_path: str, table_name: str, limit: int = 10) -> List[Dict]:
    """获取表数据预览"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_table_stats(db_path: str, table_name: str) -> Dict[str, Any]:
    """获取表统计信息"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 总行数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cursor.fetchone()[0]

    # 列信息
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    conn.close()

    return {
        "total_rows": total_rows,
        "column_count": len(columns),
        "columns": [{"name": col[1], "type": col[2]} for col in columns]
    }
