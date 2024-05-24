
import os
import subprocess
from config.config_setting import get_config
from services.vectordb_service import logging
from confluent_kafka.admin import AdminClient, NewTopic


def create_topic(topic_name, partitions, replication_factor):
    config = get_config()
    try:


        PRODUCER_CONFIG = {
            'bootstrap.servers': config.BROKERS,
        }
        admin = AdminClient(PRODUCER_CONFIG)
        topic = NewTopic(topic=topic_name, num_partitions=partitions, replication_factor=replication_factor)
        futures = admin.create_topics([topic])

        # Wait for each operation to finish
        for topic, future in futures.items():
            try:
                future.result()  # The result() method blocks until the operation is complete
                logging.info(f"Topic {topic} created successfully.")
            except Exception as e:
                logging.error(f"Failed to create topic {topic}: {e}")
    except Exception as e:
        logging.error(f"Error occurred: {e}")



def is_directory_empty(path):
    return not any(os.scandir(path))
def ensure_directory_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")


def run_recovery_command(directory, partitions):
    ensure_directory_exists(directory)
    if is_directory_empty(directory):
        command = f"python -m bytewax.recovery {directory} {partitions}"
        logging.info(f"Running command: {command}")
        subprocess.run(command, shell=True)
    else:
        logging.info(f"Directory {directory} is not empty, skipping recovery setup.")
