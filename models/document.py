from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal

class Document(BaseModel):
    """
    Class for storing a piece of text and associated metadata.
    """
    page_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    type: Literal["Document"] = "Document"

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """
        Return whether this class is serializable.
        """
        return True

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        """
        Get the namespace of the langchain object.
        """
        return ["langchain", "schema", "document"]
