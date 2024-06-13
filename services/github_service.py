from typing import Dict, Any, Generator, List, Tuple
from github import Github, Auth
from models.commit import CommitData, FileInfo
from models.document import Document
from config.config_setting import config
from icecream import ic
from utils.setup_logging import setup_logging, get_logger
from multiprocessing import Pool, cpu_count
import time

setup_logging()
logger = get_logger(__name__)


def fetch_repository(owner: str, repo_name: str) -> Any:
    """
    Fetches a GitHub repository object.

    :param owner: Owner of the repository.
    :param repo_name: Name of the repository.
    :return: Repository object if found, None otherwise.
    """
    try:
        g = Github(auth=Auth.Token(config.GITHUB_TOKEN))
        return g.get_repo(f"{owner}/{repo_name}")
    except Exception as e:
        logger.error({
            "error": "Failed to fetch repository",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        })
        return None


def create_document(file: FileInfo, event_data: CommitData) -> Document:
    """
    Creates a Document object from the provided file and commit data.

    :param file: Information about the file changed in the commit.
    :param event_data: Data about the commit.
    :return: A Document object with the combined data, or None if file contents are None.
    """
    if file.patch is None:
        return None

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


def fetch_commit_data(args: Tuple[Any, str]) -> CommitData:
    """
    Fetches commit data and returns a CommitData object.

    :param args: Tuple containing commit object and repository name.
    :return: A CommitData object with the commit information.
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


def fetch_and_emit_commits(repo_info: Dict[str, Any]) -> Generator[str, None, None]:
    """
    Fetches commits from a repository and processes them into documents.

    :param repo_info: Dictionary containing repository information.
    :return: A generator yielding JSON serialized document strings.
    """
    start_time = time.time()
    owner = repo_info["owner"]
    repo_name = repo_info["repo_name"]
    repo = fetch_repository(owner, repo_name)

    if repo is None:
        return

    commit_options = {key: value for key, value in repo_info.items() if key not in ["owner", "repo_name"]}

    try:
        commits = repo.get_commits(**commit_options)

        commit_args = zip(commits, [repo_name] * commits.totalCount)

        with Pool(processes=cpu_count()) as pool:
            all_commit_data = list(pool.imap_unordered(fetch_commit_data, commit_args))

        latest_files = {}
        for commit_data in all_commit_data:
            for file in commit_data.files:
                if file.filename not in latest_files or commit_data.date > latest_files[file.filename]['date']:
                    latest_files[file.filename] = {
                        'file': file,
                        'commit_id': commit_data.commit_id,
                        'date': commit_data.date
                    }

        documents = [
            create_document(file_info['file'], commit_data)
            for file_info in latest_files.values()
            if (commit_data := next((cd for cd in all_commit_data if cd.commit_id == file_info['commit_id']), None))
        ]

        documents = [doc for doc in documents if doc is not None]

        yield [document.model_dump_json() for document in documents]
        logger.info(f"Processed combined commit data into {len(documents)} documents for repo {repo_name}")

    except Exception as e:
        logger.error({
            "error": "Failed to fetch commits",
            "details": str(e),
            "repo": f"{owner}/{repo_name}"
        })

    finally:
        end_time = time.time()
        total_time = end_time - start_time
        logger.info(f"Total time to process commits: {total_time:.2f} seconds")
