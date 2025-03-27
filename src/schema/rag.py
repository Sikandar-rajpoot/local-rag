from pydantic import BaseModel
from typing import List, Optional, Dict

class QueryRequest(BaseModel):
    query: str
    file_paths: List[str] = []

class AutomationRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str
    context: List[str]
    metadata: List[Dict[str, str]]

class AutomationResponse(BaseModel):
    result: str

class HistoryEntry(BaseModel):
    id: int
    type: str
    query: str
    file_paths: str
    response: str
    details: Optional[str]
    timestamp: str