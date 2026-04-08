"""
文件上传路由
"""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import DataSource
from app.services.file_processor import process_file
from app.schemas.data_source import DataSourceResponse

router = APIRouter()

# 上传文件保存目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    上传 Excel/CSV 文件并创建数据源

    Args:
        file: 上传的文件
        name: 数据源名称（可选，默认使用文件名）

    Returns:
        创建的数据源信息和处理结果
    """
    # 检查文件类型
    allowed_extensions = {'.xlsx', '.xls', '.csv'}
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。仅支持: {', '.join(allowed_extensions)}"
        )

    # 生成唯一文件名
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename

    try:
        # 保存文件
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # 处理文件
        result = process_file(str(file_path))

        if not result.get('success'):
            # 处理失败，删除上传的文件
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"文件处理失败: {result.get('error', '未知错误')}"
            )

        # 创建数据源记录
        data_source = DataSource(
            id=str(uuid.uuid4()),
            name=name or Path(file.filename).stem,
            type="sqlite",
            host=result['db_path'],
            port=0,
            database_name=result['table_name'],
            username="",
            password_encrypted="",
            connection_options={
                "is_uploaded": True,
                "original_filename": file.filename,
                "uploaded_at": str(uuid.uuid4()),
                "row_count": result['row_count'],
                "column_count": result['column_count']
            },
            schema_cache=result['schema'],
            is_active=True
        )

        db.add(data_source)
        db.commit()
        db.refresh(data_source)

        return {
            "success": True,
            "data_source": {
                "id": data_source.id,
                "name": data_source.name,
                "type": data_source.type,
                "row_count": result['row_count'],
                "column_count": result['column_count'],
                "table_name": result['table_name'],
                "created_at": data_source.created_at
            },
            "preview": result.get('preview', []),
            "columns": result.get('columns', [])
        }

    except HTTPException:
        raise
    except Exception as e:
        # 清理文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/upload/preview/{source_id}")
async def preview_data(
    source_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """预览上传的数据"""
    from app.services.file_processor import get_table_preview

    data_source = db.query(DataSource).filter(
        DataSource.id == source_id,
        DataSource.is_active == True
    ).first()

    if not data_source:
        raise HTTPException(status_code=404, detail="数据源不存在")

    try:
        preview = get_table_preview(
            data_source.host,
            data_source.database_name,
            limit
        )
        return {
            "success": True,
            "data": preview,
            "columns": list(preview[0].keys()) if preview else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")
