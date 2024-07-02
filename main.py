from logging_config import setup_logging, get_logger
from utils.kafka_setup import run_recovery_command
import os

setup_logging()
logger = get_logger(__name__)


def main():
    recovery_directories = {
        "recovery/github_listener": 4,
        "recovery/commit_summary_service": 4,
        "recovery/add_qdrant_service": 4,
        "recovery/gateway_service": 4,
        "recovery/pdf_service": 4
    }
    for directory, partitions in recovery_directories.items():
        if not os.path.exists(directory) or not os.listdir(directory):
            run_recovery_command(directory, partitions)


if __name__ == "__main__":
    main()
