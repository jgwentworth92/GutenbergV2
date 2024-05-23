from config.config_setting import get_config
from utils.kafka_setup import run_recovery_command, create_topic


def main():
    recovery_directories = {
        "recovery/github_listener": 4,
        "recovery/commit_summary_service": 4,
        "recovery/add_qdrant_service": 4
    }
    config=get_config()
    create_topic(config.INPUT_TOPIC, 4, 3)
    create_topic(config.OUTPUT_TOPIC, 4, 3)
    create_topic(config.PROCESSED_TOPIC, 4, 3)
    create_topic(config.VECTORDB_TOPIC_NAME, 4, 3)
    for directory, partitions in recovery_directories.items():
        run_recovery_command(directory, partitions)

if __name__ == "__main__":
    main()
