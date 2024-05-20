from pydantic import BaseModel
from typing import List, Optional

class FileInfo(BaseModel):
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None

class CommitData(BaseModel):
    author: str
    message: str
    date: str
    url: str
    repo_name: str
    commit_id: str
    files: List[FileInfo]
