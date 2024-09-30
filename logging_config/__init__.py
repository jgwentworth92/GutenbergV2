"""
Logging configuration for application
"""
import logging
import os
import sys
import multiprocessing

from logging.config import dictConfig

from config.config_setting import get_config

config = get_config()
APP_NAME = config.APP_NAME
LOG_DIR = config.LOG_DIRECTORY
DEUBG = config.DEBUG

# Create log directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logging():
    """ 
    Setup logging configuration
    """
    dictConfig(LOGGING_CONFIG)

def get_logger(logger_name=APP_NAME, module_name=None):
    """
    Get logger by name or module name
    """
    if module_name:
        return logging.getLogger(logger_name or APP_NAME).getChild(module_name)
    else:
        return logging.getLogger(logger_name)
# Define the logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    # define the format of the log messages
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    # define handlers
    'handlers': {
        'console': {
            # log to stdout
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
            'level': 'DEBUG',
        },
        # RotatingFileHandler allows for log rotation after a certain size
        'file':{
            'class': 'logging.handlers.RotatingFileHandler',
            # for now, using standard formatter
            'formatter': 'standard',
            'filename': os.path.join(LOG_DIR, f'{APP_NAME}.log'),
            'maxBytes': 5000000,
            'backupCount': 5,
        },

    },
    # defining loggers
    'loggers': {
        # root logger
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        # app logger
        f'{APP_NAME}': {
            'handlers': ['console','file'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}
