from typing import Dict, Any, Generator, List
from models.commit import CommitData, FileInfo
from langchain_core.documents import Document
from icecream import ic
from config.config_setting import config
from utils.model_utils import setup_chat_model


def create_documents(event_data: Dict[str, Any]) -> List[Document]:
    documents = []
    for file in event_data['files']:
        doc = create_document(file, event_data)
        documents.append(doc)
    return documents


def create_document(file: Dict[str, Any], event_data: Dict[str, Any]) -> Document:
    validated_file = FileInfo(**file)
    validated_event = CommitData(**event_data)
    page_content = f"Filename: {validated_file.filename}, Status: {validated_file.status}, Files: {validated_file.patch}"
    metadata = {
        "filename": validated_file.filename,
        "status": validated_file.status,
        "additions": validated_file.additions,
        "deletions": validated_file.deletions,
        "changes": validated_file.changes,
        "author": validated_event.author,
        "date": validated_event.date,
        "repo_name": validated_event.repo_name,
        "commit_url": validated_event.url,
        "id": validated_event.commit_id,
        "token_count": len(page_content.split())
    }
    return Document(page_content=page_content, metadata=metadata)


def process_message(message: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
    if "error" in message:
        ic(f"Error in message: {message}")
        return

    event_data = message
    try:
        documents = create_documents(event_data)

        for doc in documents:
            try:
                chain = setup_chat_model()
                summary = chain.invoke({"text": doc.page_content})
                updated_doc = Document(page_content=" Summary: " + summary, metadata=doc.metadata)
                yield {"page_content": doc.page_content,
                       "metadata": doc.metadata}
                yield {"page_content": updated_doc.page_content,
                       "metadata": updated_doc.metadata}
                ic(updated_doc.page_content)
                ic("___________________ summary content end___________")
                ic(f"metadata of commit {doc.metadata}")
            except Exception as e:
                error_message = {
                    "error": "Failed to process document",
                    "details": str(e),
                    "document_metadata": doc.metadata
                }
                ic(error_message)
                yield error_message
    except Exception as e:
        error_message = {
            "error": "Failed to create documents",
            "details": str(e),
            "event_data": event_data
        }
        ic(error_message)
        yield error_message
