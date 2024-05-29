FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Set up a workdir where we can put our dataflow
WORKDIR /bytewax
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create recovery directories for each service
RUN mkdir -p /bytewax/recovery/github_listener /bytewax/recovery/commit_summary_service  /bytewax/recovery/add_qdrant_service

# Copy requirements file and install dependencies
COPY ./requirements.txt /bytewax/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Initialize Bytewax recovery partitions

# Set PYTHONUNBUFFERED to any value to make Python flush stdout
CMD ["python", "main.py"]