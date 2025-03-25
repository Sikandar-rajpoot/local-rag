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
