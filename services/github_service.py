from typing import Dict, Any, Generator, List
from github import Github, Auth, Commit
from langchain_core.documents import Document
from models.commit import CommitData, FileInfo
from config.config_setting import config
from icecream import ic
from utils.setup_logging import setup_logging, get_logger
from multiprocessing import Pool

setup_logging()
logger = get_logger(__name__)

def create_documents(event_data: CommitData) -> List[Document]:
    return [create_document(file, event_data) for file in event_data.files]

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
        "token_count": len(page_content.split()),
        "collection_name": f"{event_data.repo_name}",
        "vector_id": event_data.commit_id + file.filename
    }
    return Document(page_content=page_content, metadata=metadata)

def fetch_commit_data(args) -> CommitData:
    commit, repo_name = args
    return CommitData(
        author=commit.commit.author.name,
        message=commit.commit.message,
        date=commit.commit.author.date.isoformat(),
        url=commit.html_url,
        repo_name=repo_name,
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

def fetch_and_emit_commits(repo_info: Dict[str, str]) -> Generator[Dict[str, Any], None, None]:
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
        return

    try:
        commits = repo.get_commits()  # Use generator to avoid loading all commits into memory
        with Pool() as pool:
            commit_args = ((commit, repo_name) for commit in commits)
            for commit_data in pool.imap_unordered(fetch_commit_data, commit_args):
                logger.info(f"Processed commit ID {commit_data.commit_id} for repo {commit_data.repo_name}")
                documents = create_documents(commit_data)
                yield {"documents": [{"page_content": document.page_content, "metadata": document.metadata} for document in documents]}
                logger.info(f"Processed commit data into {len(documents)} documents for repo {commit_data.repo_name}")
    except Exception as e:
        error_message = {
            "error": "Failed to fetch commits",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        logger.error(error_message)
        return
