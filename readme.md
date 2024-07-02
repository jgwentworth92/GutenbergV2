
# Gutenberg

---

The project aims to develop an automated system capable of grading GitHub repositories and transforming various data types into actionable insights. The system leverages modern stream processing frameworks, microservices, and local large language models (LLMs) to ensure scalability, efficiency, and cost-effectiveness.

---

## Table of Contents

  - [Features](#features)
  - [Project Structure](#project-structure)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
  - [Running the Dataflows Manually](#running-the-dataflows-manually)
  - [Testing](#testing)

## Features

- Fetch commits from GitHub repositories
- Process commit messages to generate summaries
- Store results in a vector database
- Kafka integration for message streaming
- Configurable to use different chat models and providers (OpenAI, Fake model, local model)
- Kafka KRaft instance for broker management
- Kafka UI for cluster management
- REST Proxy for interacting with Kafka topics via REST API
- Schema Registry for managing Kafka message schemas
- FastAPI application for user and job CRUD operations
- Debezium for change data capture from PostgreSQL to Kafka
- Streamlit frontend for job submission and document viewing

## Project Structure

```
gutenberg/
├── config/
│   ├── __init__.py
│   └── config_setting.py
├── dataflow_connectors/
│   └── fastapi_connector.py
├── dataflows/
│   ├── __init__.py
│   ├── add_qdrant_service.py
│   ├── commit_summary_service.py
│   ├── gateway_service.py
│   ├── github_commit_processing.py
│   └── pdfProcessing.py
├── debezium-setup/
│   ├── connector-config.json
│   └── init-connector-config.sh
├── kui/
│   └── config.yml
├── logging_config/
│   └── __init__.py
├── models/
│   ├── __init__.py
│   ├── commit.py
│   ├── document.py
│   └── gateway.py
├── services/
│   ├── __init__.py
│   ├── github_service.py
│   ├── message_processing_service.py
│   ├── pdf_processing_service.py
│   └── vectordb_service.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── intergration_tests/
│   │   ├── __init__.py
│   │   ├── test_debezium.py
│   │   ├── test_kafka_github.py
│   │   └── test_kafka_pdf.py
│   └── unit_tests/
│       ├── __init__.py
│       ├── test_fast_api_connector.py
│       ├── test_gateway_service.py
│       ├── test_github_service.py
│       ├── test_llm_service.py
│       ├── test_pdf_service.py
│       └── test_qdrant_services.py
├── utils/
│   ├── __init__.py
│   ├── dataflow_processing_utils.py
│   ├── get_qdrant.py
│   ├── kafka_setup.py
│   ├── kafka_utils.py
│   ├── langchain_callback_logger.py
│   └── model_utils.py
├── docker-compose.yml
├── init.sql
├── main.py
├── pytest.ini
├── README.md
└── requirements.txt
```

## Prerequisites

- Python
- Git
- Docker

## Installation

1. **Clone the repository and switch to this branch (feat-custom-fastapi-sink):**
   ```sh
   git clone https://github.com/jgwentworth92/GutenbergV2.git
   cd GutenbergV2
   git checkout -b feat-custom-fastapi-sink origin/feat-custom-fastapi-sink
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

4. **Set up your environment variables:**
   Create a `.env` file in the root directory and add the required environment variables:
    ```env
   GITHUB_TOKEN=[your_github_token]
   BROKERS="kafka_b:9094"
   INPUT_TOPIC=repos-topic
   OUTPUT_TOPIC=github-commits-out
   PROCESSED_TOPIC=addtovectordb
   CONSUMER_CONFIG={"bootstrap.servers": "kafka_b:9094","auto.offset.reset": "earliest","group.id": "consumer_group","enable.auto.commit": "True"}
   PRODUCER_CONFIG={"bootstrap.servers": "kafka_b:9094"}
   OPENAI_API_KEY=your_openai_api_key
   TEMPLATE = "You are an assistant whose job is to create detailed descriptions of what the provided code files do.Please review the code below and explain its functionality in detail.Code:{text}"
   VECTORDB_TOPIC_NAME="QdrantOutput"
   POSTGRES_HOSTNAME=postgres
   POSTGRES_PORT=5432
   POSTGRES_USER=[user]
   POSTGRES_DB=myappdb
   POSTGRES_PASSWORD=[password]
   RESOURCE_TOPIC=resource_topic
   PDF_INPUT=pdfInput
   MODEL_PROVIDER="fake"
   LOCAL_LLM_URL = "http://[your_ip_address]:1234/v1"
   smtp_username=[username]
   smtp_password=[password]
   GITHUB_TOPIC=github_topic
   MAILTRAP_USERNAME=[your_mailtrap_username]
   MAILTRAP_PASSWORD=[your_mailtrap_password]
   ```

5. **Add Streamlit frontend to docker-compose.yml:**
   Add the following service to your `docker-compose.yml` file:
   ```yaml
   streamlit:
     image: jgcapworh92/gutenberg-streamlit-frontend:latest
     container_name: streamlit_frontend
     ports:
       - "8501:8501"
     environment:
       - API_URL=http://fastapi:8000
     depends_on:
       - fastapi
     restart: always
   ```

Note: The system will automatically create recovery partitions if they are not manually created when the project is started.

### Using OpenAI
1. **Set up OpenAI API key:**
   Create an account on OpenAI and get an API key. Add the key to the `.env` file.
2. **Set the model provider to OpenAI:**
   Set the `MODEL_PROVIDER` environment variable to `openai` in the `.env` file.

### Using a Local Model

The system is known to work with LMStudio, but it should theoretically work with any OpenAI API-compatible system.

1. **Set up the local model:**
   Install LMStudio (or another backend) and turn on the server. [Here is a tutorial](https://www.youtube.com/watch?v=yBI1nPep72Q). Recommended model: `lmstudio-community/Mistral-7B-Instruct-v0.3-GGUF`
2. **Set the model provider to Local:**
   Set the `MODEL_PROVIDER` environment variable to `lmstudio` in the `.env` file.
3. **Set the local model URL:**
   Set the `LOCAL_LLM_URL` environment variable to the URL of the local model server in the `.env` file. In the case of LMStudio, the URL is `http://[your_ip_address]:1234/v1`. Make sure to use the correct IP address for your computer, as Docker containers cannot access `localhost`.

### Using a Fake Model

The fake model enables the system to bypass the use of a real API. It's a straightforward and rapid solution, making it particularly useful for testing purposes.

1. **Set the model provider to Fake:**
   Set the `MODEL_PROVIDER` environment variable to `fake` in the `.env` file.

## Usage

To start all services, navigate to the root directory of your project where the `docker-compose.yml` file is located and run the following command:

```bash
docker-compose up --build
```

This will build and start all the services required, including running the Alembic migration scripts automatically.

### Accessing the Services

1. **Kafka UI:** Access at [http://localhost:8080/](http://localhost:8080/)

2. **Gutenberg Ingestion API:** Access the FastAPI Swagger UI at [http://localhost:8000/docs](http://localhost:8000/docs)
   - This API provides routes for user and job CRUD operations.
   - Users can submit jobs to start event-driven microservices.
   - The FastAPI app adds entries to the PostgreSQL database.
   - Debezium watches the resource table and produces changes to a Kafka topic.
   - For more detailed information about the Gutenberg Ingestion API, please visit: [https://github.com/jgwentworth92/Gutenberg-Ingestion-API](https://github.com/jgwentworth92/Gutenberg-Ingestion-API)

3. **Streamlit Frontend:** Access at [http://localhost:8501](http://localhost:8501)
   - Use this frontend to submit and view documents in the system.

4. **Qdrant Web UI:** Access at [http://localhost:6333/dashboard#/collections](http://localhost:6333/dashboard#/collections)
   - Use this to view generated summaries.

### User Registration and Job Submission

1. Register a new user through the FastAPI or Streamlit interface.
2. You will receive a verification email in your Mailtrap.io inbox.
3. Log in to Mailtrap.io and manually verify the user by clicking the verification link in the test email.
4. After verification, you can log in to the system and submit jobs.

### Adding a GitHub Repository

1. Open the Kafka Web UI at [http://localhost:8080/](http://localhost:8080/)

2. Select "Topics" from the left-hand menu. If the menu is hidden, click on the hamburger icon on the top left.

3. Click on "repos-topic" from the list of topics.

4. Click on the "Produce Message" button on the top right.

5. Enter the GitHub repo owner and URL in the "Value" field, in this format:

    ```json
    {
	"owner": "octocat",
	"repo_name": "Hello-World"
    }
    ```
   Make sure it is a public repo, or it is a repo you currently have access to via the GitHub token in the `.env` file. Leave all other values as default.

6. Click on the "Produce Message" button at the bottom of the dialog to add the repo to the topic.

The system will automatically process the repo and generate summaries using the LLM, via the provider specified in the `.env` file.

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


