# Gutenberg

---

The project aims to develop an automated system capable of grading GitHub repositories and transforming various data types into actionable insights. The system leverages modern stream processing frameworks, microservices, and local large language models (LLMs) to ensure scalability, efficiency, and cost-effectiveness.

---


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
  - [Additional Services](#additional-services)
    - [Kafka UI](#kafka-ui)
    - [Qdrant Web UI](#qdrant-web-ui)

## Features

- Fetch commits from GitHub repositories
- Process commit messages to generate summaries
- Store results in a vector database
- Kafka integration for message streaming
- Configurable to use different chat models and providers (OpenAI, Fake model, LMStudio)
- Kafka KRaft instance for broker management
- Kafka UI for cluster management
- REST Proxy for interacting with Kafka topics via REST API
- Schema Registry for managing Kafka message schemas

## Project Structure

```
my_project/
├── config/
│   ├── __init__.py
│   ├── config_setting.py
├── models/
│   ├── __init__.py
│   ├── commit.py
├── services/
│   ├── __init__.py
│   ├── github_service.py
│   ├── message_processing_service.py
│   ├── vectordb_service.py
├── utils/
│   ├── __init__.py
│   ├── kafka_utils.py
│   ├── model_utils.py
│   ├── get_qdrant.py
│   ├── setup_logging.py
├── dataflows/
│   ├── __init__.py
│   ├── github_commit_processing.py
│   ├── commit_summary_service.py
│   ├── add_qdrant_service.py
├── tests/
│   ├── __init__.py
│   ├── test_github_service.py
│   ├── test_message_processing_service.py
│   ├── test_dataflows.py
└── requirements.txt
```

## Pre-requisites

- Python
- Git
- Docker

## Setup and Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/jgwentworth92/GutenbergV2.git
   cd GutenbergV2
   ```

2. **Create and activate a virtual environment according to your operating system:**

   1. **On Linux:**
      ```sh
      python -m venv venv
      source venv/bin/activate  
      ```
   
   2. **On Windows:**
      ```sh
      python -m venv venv
      venv\Scripts\activate
      ```


3. **Install the dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Create the recovery partitions**:

    Create the necessary directories for the recovery partitions:

   ```sh
   mkdir recovery
   cd recovery
   mkdir github_listener
   mkdir commit_summary_service
   mkdir add_qdrant_service
   cd ..
   ```

    Set up recovery partitions for each microservice:

   ```sh
   python -m bytewax.recovery recovery/github_listener
   python -m bytewax.recovery recovery/commit_summary_service
   python -m bytewax.recovery recovery/add_qdrant_service
   ```

    This ensures that Bytewax can recover from failures and continue processing. 


5. **Set up your environment variables:**
   Create a `.env` file in the root directory and add the required environment variables:
    ```env
   GITHUB_TOKEN=your_github_token
   BROKERS="localhost:9092"
   INPUT_TOPIC=your_input_topic
   OUTPUT_TOPIC=your_output_topic
   PROCESSED_TOPIC=your_processed_topic
   VECTORDB_TOPIC_NAME=your_vectordb_topic_name
   CONSUMER_CONFIG={"bootstrap.servers": "kafka_b:9094","auto.offset.reset": "earliest","group.id": "consumer_group","enable.auto.commit": "True"}
   PRODUCER_CONFIG={"bootstrap.servers": "kafka_b:9094"}
   OPENAI_API_KEY=your_openai_api_key
   MODEL_PROVIDER=openai
   TEMPLATE=your_template_string
   LOCAL_LLM_URL = "http://[your_ip_address]:1234/v1"
   ```

## Running

To start all services, navigate to the root directory of your project where the `docker-compose.yml` file is located and run the following command:

```bash
docker-compose up --build
```

This will build and start all the services required.

The Kafka UI is used to import repos to process. It can be accessed at [http://localhost:8080/](http://localhost:8080/). 

### In order to add a repo:

1. Open the Web UI


2. Select "Topics" from the left-hand menu. If the menu is hidden, click on the hamburger icon on the top left.


3. Click on "repos-topic" from the list of topics.


4. Click on the "Produce Message" button on the top right.


5. Enter the GitHub repo URL in the "Message Value" field, with this format:

    ```json
    {
	\\"owner": "octocat",
	\\"repo_name": "Hello-World"
    }
    ```
   Make sure it is a public repo, or it is a repo you currently have access to via the GitHub token in the `.env` file.


6. Click on the "Produce Message" button at the bottom of the dialog to add the repo to the topic.

The system will automatically process the repo and generate summaries using the LLM, via the provider specified in the `.env` file.

The Qdrant Web UI is used to see the generated summaries. It can be accessed at [http://localhost:6333/dashboard#/collections](http://localhost:6333/dashboard#/collections).

## Configuration

The application configuration is managed using Pydantic settings. Modify the `config/config_setting.py` file to update the configuration settings.


## Running the Dataflows Manually

The system runs the dataflows automatically. To run the dataflows manually, use the following command format, replacing `(filename)` with the actual filename of the dataflow script without the `.py` extension:

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


## Testing

To run the tests, use the `pytest` framework:

```sh
pytest .
```

The tests are located in the `tests/` directory and cover the GitHub service, message processing service, and dataflows.
