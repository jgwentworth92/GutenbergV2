import logging
import logging.config
import os

def setup_logging(config_path='logging.conf'):
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path)
    else:
        raise FileNotFoundError(f"Logging configuration file not found: {config_path}")

def get_logger(name):
    return logging.getLogger(name)

# Example usage:
