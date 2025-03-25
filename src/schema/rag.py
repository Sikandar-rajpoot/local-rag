from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    file_path: str

class QueryResponse(BaseModel):
    response: str
    context: list[str]
    metadata: list[dict]