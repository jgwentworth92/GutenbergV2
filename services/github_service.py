from github import Github, Auth
from models.commit import CommitData, FileInfo
from config.config_setting import config
from icecream import ic

from utils.setup_logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
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
                yield commit_data.model_dump()
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
