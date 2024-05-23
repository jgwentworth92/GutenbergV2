# Gutenberg

This project is a Kafka consumer application that processes GitHub commit data, generates summaries using a chat model, and stores the results in a vector database. The application is built using Bytewax for data processing and Kafka for message streaming.

## Table of Contents

- [Kafka Consumer with Vector Database Additions](#kafka-consumer-with-vector-database-additions)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Setup and Installation](#setup-and-installation)
  - [Configuration](#configuration)
  - [Running the Services](#running-the-services)
  - [Running the Dataflows](#running-the-dataflows)
  - [Creating Recovery Partitions](#creating-recovery-partitions)
  - [Testing](#testing)

## Features

- Fetch commits from GitHub repositories
- Process commit messages to generate summaries
- Store results in a vector database
- Kafka integration for message streaming
- Configurable to use different chat models (OpenAI, Fake model)

## Project Structure


 ```
my_project/
├── config/
│ ├── init.py
│ ├── config_setting.py
├── models/
│ ├── init.py
│ ├── commit.py
├── services/a
│ ├── init.py
│ ├── github_service.py
│ ├── message_processing_service.py
│ ├── vectordb_service.py
├── utils/
│ ├── init.py
│ ├── kafka_utils.py
│ ├── model_utils.py
│ ├── get_qdrant.py
│ ├── setup_logging.py
├── dataflows/
│ ├── init.py
│ ├── github_commit_processing.py
│ ├── commit_summary_service.py
│ ├── add_qdrant_service.py
├── tests/
│ ├── init.py
│ ├── test_github_service.py
│ ├── test_message_processing_service.py
│ ├── test_dataflows.py
└── requirements.txt
```

## Setup and Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/jgwentworth92/GutenbergV2.git
   cd your-repo
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up your environment variables:**
   Create a `.env` file in the root directory and add the required environment variables:
   ```env
   GITHUB_TOKEN=your_github_token
   BROKERS=your_kafka_broker
   INPUT_TOPIC=your_input_topic
   OUTPUT_TOPIC=your_output_topic
   PROCESSED_TOPIC=your_processed_topic
   VECTORDB_TOPIC_NAME=your_vectordb_topic_name
   VECTOR_DB_HOST=your_vectordb_host
   VECTOR_DB_PORT=your_vectordb_port
   CONSUMER_CONFIG={"group.id": "your_group_id", "auto.offset.reset": "earliest"}
   PRODUCER_CONFIG={"acks": "all"}
   OPENAI_API_KEY=your_openai_api_key
   MODEL_PROVIDER=openai
   TEMPLATE=your_template_string
   ```

## Configuration

The application configuration is managed using Pydantic settings. Modify the `config/config_setting.py` file to update the configuration settings.

## Running the Services

To start all services, navigate to the root directory of your project where the `docker-compose.yml` file is located and run the following command:

```bash
docker-compose up --build
```

This will build and start all the services defined in your `docker-compose.yml` file.

## Running the Dataflows

To run the dataflows, use the following command format, replacing `(filename)` with the actual filename of the dataflow script without the `.py` extension:

```sh
python -m bytewax.run -w3 dataflows.(filename)
```

For example, to run the GitHub commit processing dataflow:

```sh
python -m bytewax.run -w3 dataflows.github_commit_processing
```

And to run the commit summary service dataflow:

```sh
python -m bytewax.run -w3 dataflows.commit_summary_service
```

And to run the add to Qdrant service dataflow:

```sh
python -m bytewax.run -w3 dataflows.add_qdrant_service
```

## Creating Recovery Partitions

Before creating recovery partitions, ensure that the necessary directories exist. If not, create them:

```sh
mkdir -p recovery/github_listener
mkdir -p recovery/commit_summary_service
mkdir -p recovery/add_qdrant_service
```

To set up recovery partitions for each microservice, run the following commands. This ensures that Bytewax can recover from failures and continue processing.

1. **GitHub Commit Processing Recovery Partition:**
   ```sh
   python -m bytewax.recovery recovery/github_listener 4
   ```

2. **Commit Summary Service Recovery Partition:**
   ```sh
   python -m bytewax.recovery recovery/commit_summary_service 4
   ```

3. **Add to Qdrant Service Recovery Partition:**
   ```sh
   python -m bytewax.recovery recovery/add_qdrant_service 4
   ```

These commands should be run from the root directory of your project.

## Testing

To run the tests, use the `pytest` framework:

```sh
pytest .
```

The tests are located in the `tests/` directory and cover the GitHub service, message processing service, and dataflows.

