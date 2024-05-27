from typing import Dict, Any, List

from github import Github, Auth
from langchain_core.documents import Document

from models.commit import CommitData, FileInfo
from config.config_setting import config
from icecream import ic

from utils.setup_logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def create_documents(event_data: Dict[str, Any]) -> List[Document]:
    commit_data = CommitData(**event_data)
    documents = []
    for file in commit_data.files:
        doc = create_document(file, commit_data)
        documents.append(doc)
    return documents

def create_document(file: FileInfo, event_data: CommitData) -> Document:
    page_content = f"Filename: {file.filename}, Status: {file.status}, Files: {file.patch}"
    metadata = {
        "filename": file.filename,
        "status": file.status,
        "additions": file.additions,
        "deletions": file.deletions,
        "changes": file.changes,
        "author": event_data.author,
        "date": event_data.date,
        "repo_name": event_data.repo_name,
        "commit_url": event_data.url,
        "id": event_data.commit_id,
        "token_count": len(page_content.split())
    }
    return Document(page_content=page_content, metadata=metadata)
def fetch_and_emit_commits(repo_info):
    owner = repo_info["owner"]
    repo_name = repo_info["repo_name"]
    token = config.GITHUB_TOKEN
    g = Github(auth=Auth.Token(token))

    logger.info(f"Fetching repository {owner}/{repo_name}")
    try:
        repo = g.get_repo(f"{owner}/{repo_name}")
    except Exception as e:
        error_message = {
            "error": "Failed to fetch repository",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        logger.error(error_message)
        yield error_message
        return

    try:
        for commit in repo.get_commits():
            try:
                commit_data = CommitData(
                    author=commit.commit.author.name,
                    message=commit.commit.message,
                    date=commit.commit.author.date.isoformat(),
                    url=commit.html_url,
                    repo_name=repo.name,
                    commit_id=commit.sha,
                    files=[FileInfo(
                        filename=file.filename,
                        status=file.status,
                        additions=file.additions,
                        deletions=file.deletions,
                        changes=file.changes,
                        patch=getattr(file, 'patch', None)
                    ) for file in commit.files]
                )
                logger.info(f"Processed commit ID {commit_data.commit_id} for repo {commit_data.repo_name}")
                documents = create_documents(commit_data.model_dump())
                for document in documents:
                    logger.info(f"Processed commit data into document with {document.metadata} for repo {commit_data.repo_name}")

                    yield {"page_content": document.page_content,
                           "metadata": document.metadata}
            except Exception as e:
                error_message = {
                    "error": "Failed to process commit",
                    "details": str(e),
                    "commit_id": commit.sha
                }
                logger.error(error_message)
                yield error_message
    except Exception as e:
        error_message = {
            "error": "Failed to fetch commits",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        logger.error(error_message)
        yield error_message
