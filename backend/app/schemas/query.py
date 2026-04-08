from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class QueryExecuteRequest(BaseModel):
    sql: str
    data_source_id: Optional[str] = None


class QueryExecuteResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: int
    sql: str