from typing import Dict, Any, Generator, List, Tuple
from github import Github, Auth, Commit
from models.commit import CommitData, FileInfo
from models.document import Document  # Import the Pydantic Document class
from config.config_setting import config
from icecream import ic
from utils.setup_logging import setup_logging, get_logger
from multiprocessing import Pool
import time

setup_logging()
logger = get_logger(__name__)

def create_documents(event_data: CommitData) -> List[Document]:
    """
    Creates a list of Document objects from the given commit data.

    Args:
        event_data (CommitData): The commit data containing file changes and metadata.

    Returns:
        List[Document]: A list of Document objects created from the commit data.
    """
    return [create_document(file, event_data) for file in event_data.files]

def create_document(file: FileInfo, event_data: CommitData) -> Document:
    """
    Creates a Document object from a single file and commit data.

    Args:
        file (FileInfo): Information about the file changes in the commit.
        event_data (CommitData): The commit data containing metadata.

    Returns:
        Document: A Document object created from the file and commit data.
    """
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
    """
    Fetches commit data and creates a CommitData object from it.

    Args:
        args (Tuple[Commit, str]): A tuple containing the commit object and the repository name.

    Returns:
        CommitData: A CommitData object created from the commit and repository information.
    """
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

def fetch_and_emit_commits(repo_info: Dict[str, str]) -> Generator[str, None, None]:
    """
    Fetches commits from a GitHub repository and processes them into documents.

    Args:
        repo_info (Dict[str, str]): A dictionary containing repository information with keys 'owner' and 'repo_name'.

    Yields:
        Generator[str, None, None]: A generator yielding JSON strings of processed documents.
    """
    start_time = time.time()
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
                yield [document.model_dump_json() for document in documents]
                logger.info(f"Processed commit data into {len(documents)} documents for repo {commit_data.repo_name}")
    except Exception as e:
        error_message = {
            "error": "Failed to fetch commits",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        }
        logger.error(error_message)
        return
    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process commits: {total_time:.2f} seconds")


