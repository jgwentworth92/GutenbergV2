import json
import logging
from logging import Formatter

class JsonFormatter(Formatter):
    """
    Custom JSON formatter for logging requests and responses
    """
    def __init__(self):
        super(JsonFormatter, self).__init__()
    
    def format(self, record):
        """
        Format the log record
        """
        json_record = {}
        json_record["message"] = record.getMessage()
        if "request" in record.__dict__:
            json_record["request"] = json.dumps(record.__dict__["request"])
        if "response" in record.__dict__:
            json_record["response"] = json.dumps(record.__dict__["response"])
        if record.levelno == logging.ERROR and "exc_info" in record.__dict__:
            json_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(json_record)