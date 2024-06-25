import random
import string
import time

from starlette.middleware.base import BaseHTTPMiddleware
from appfrwk.logging_config import get_logger

class LogMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log requests and responses
    """
    async def dispatch(self, request, call_next):
        """
        Dispatch requests and log them
        """
        # Log the request
        response = await self.log_requests(request, call_next)
        return response

    async def log_requests(self, request, call_next):
        """
        Log requests
        """
        # Initialize loggers
        request_logger = get_logger('request')
        request_processing_logger = get_logger('request_processing')
        # Skip logging for requests to favicon.ico
        if request.url.path == "/favicon.ico":
            response = await call_next(request)
            return response

        # Generate a unique request id
        rid = self.generate_unique_request_id()

        # Log the start of the request
        self.log_request_start(request, rid, request_processing_logger)
        
        # Record the start time of the request
        start_time = time.monotonic()

        # Process the request
        response = await call_next(request)

        # Log the details of the request
        self.log_request_details(request, response, rid, request_logger)

        # Log the end of the request with additional info
        self.log_request_end(response, rid, start_time, request_processing_logger)

        return response
    
    def generate_unique_request_id(self):
        """
        Generate a unique request id
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def log_request_details(self, request, response, rid, logger):
        """
        Log the details of the request
        """
        logger.info(
            f"Rid={rid}",
            extra={
                "request": {
                    "url": str(request.url), 
                    "remote_address": request.client.host,
                    "method": request.method,
                    "path": request.url.path,
                    "ip": request.headers.get("X-Forwarded-For", request.client.host),
                    "host": request.headers.get("host", "unknown"),
                    "request_args": dict(request.query_params),
                    },
                "response": {"status_code": response.status_code},
            },
        )

    def log_request_start(self, request, rid, logger):
        """
        Log the start of the request
        """
        logger.info(f"Received rid={rid} Starting path={request.url.path}")

    def log_request_end(self, response, rid, start_time, logger):
        """
        Log the end of the request
        """
        # Calculate the time taken to process the request
        process_time = (time.monotonic() - start_time) * 1000
        # Format the time taken to process the request
        formatted_process_time = "{:.2f}".format(process_time)
        # Log the end of the request and the time taken to process it
        logger.info(f"Ended rid={rid} Time to process={formatted_process_time}ms Status Code={response.status_code}")