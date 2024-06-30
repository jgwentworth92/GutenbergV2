import time
from multiprocessing import Pool, cpu_count
from typing import Dict, Any, Generator, Tuple
from github import Github, Auth
from orjson import orjson
from config.config_setting import config
from logging_config import get_logger
from models.commit import CommitData, FileInfo
from models.document import Document

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


def create_document(file: FileInfo, event_data: CommitData, job_id: str) -> Document:
    """
    Creates a Document object from the provided file, commit data, and job ID.

    :param file: Information about the file changed in the commit.
    :param event_data: Data about the commit.
    :param job_id: The job ID to be passed along to the next service.
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
        "job_id": job_id,  # Include the job ID here
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


def fetch_all_commit_data(commits, repo_name):
    commit_args = zip(commits, [repo_name] * commits.totalCount)
    with Pool(processes=cpu_count()) as pool:
        return list(pool.imap_unordered(fetch_commit_data, commit_args))


def get_latest_files(all_commit_data):
    latest_files = {}
    for commit_data in all_commit_data:
        for file in commit_data.files:
            if file.filename not in latest_files or commit_data.date > latest_files[file.filename]['date']:
                latest_files[file.filename] = {
                    'file': file,
                    'commit_id': commit_data.commit_id,
                    'date': commit_data.date
                }
    return latest_files


def create_documents(latest_files, all_commit_data, job_id):
    documents = []
    for file_info in latest_files.values():
        commit_data = next((cd for cd in all_commit_data if cd.commit_id == file_info['commit_id']), None)
        if commit_data:
            document = create_document(file_info['file'], commit_data, job_id)
            if document:
                documents.append(document)
    return documents



def fetch_and_emit_commits(resource_data: Dict[str, Any]) -> Generator[str, None, None]:
    start_time = time.time()
    repo_info = orjson.loads(resource_data["resource_data"])
    job_id = resource_data["job_id"]
    owner = repo_info["owner"]
    repo_name = repo_info["repo_name"]
    repo = fetch_repository(owner, repo_name)

    if not repo:
        logger.error(f"Failed to fetch repository {owner}/{repo_name}")
        return

    commit_options = {key: value for key, value in repo_info.items() if key not in ["owner", "repo_name"]}

    try:
        commits = repo.get_commits(**commit_options)
        all_commit_data = fetch_all_commit_data(commits, repo_name)
        latest_files = get_latest_files(all_commit_data)
        documents = create_documents(latest_files, all_commit_data,job_id)

        for document in documents:
            yield document.model_dump_json()
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
