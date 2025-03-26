from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    file_path: str

class AutomationRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str
    context: list[str]
    metadata: list[dict]

class AutomationResponse(BaseModel):
    result: str

class HistoryEntry(BaseModel):
    id: int
    type: str
    query: str
    file_path: str
    response: str
    timestamp: str