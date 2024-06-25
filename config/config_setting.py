import os
import json
from functools import lru_cache
from pydantic import ConfigDict
from typing import Optional, Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Base Configuration Class"""

    APP_NAME: str = "Kafka Consumer with vector data base additions"
    TITLE: str = "Kafka Consumer Vector DB ingestors"
    DESCRIPTION: str = "Service consuming Kafka topics and adding to vector db."
    VECTOR_DB_HOST: str = "qdrant"
    VECTOR_DB_PORT: int = 6333
    GITHUB_TOKEN: Optional[str]
    BROKERS: Optional[str] = None
    INPUT_TOPIC: Optional[str] = None
    OUTPUT_TOPIC: Optional[str] = None
    RESOURCE_TOPIC: Optional[str] = "resource_topic"
    GITHUB_TOPIC: Optional[str] = "github_topic"
    PDF_INPUT: Optional[str] = None
    CONSUMER_CONFIG: Optional[Dict[str, str]] = None
    PRODUCER_CONFIG: Optional[Dict[str, str]] = None
    MODEL_PROVIDER: Optional[str] = "fake"
    TEMPLATE: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    PROCESSED_TOPIC: Optional[str] = None
    VECTORDB_TOPIC_NAME: Optional[str] = "vectordb_added_doc"
    LOCAL_LLM_URL: str
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra=None)
    USER_MANAGEMENT_SERVICE_URL: Optional[str] = "http://fastapi:8000"

    @classmethod
    def parse_env_var(cls, value: str) -> Dict[str, str]:
        return json.loads(value)


class ProductionConfig(Settings):
    pass


class DevelopmentConfig(Settings):
    DEBUG: bool = True


class TestingConfig(Settings):
    TESTING: bool = True
    DEBUG: bool = True
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_HOSTNAME: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "db"


@lru_cache()
def get_config() -> Settings:
    """Get the current configuration object"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "development":
        return DevelopmentConfig()
    elif environment == "testing":
        return TestingConfig()
    elif environment == "production":
        return ProductionConfig()
    else:
        raise ValueError(f"Invalid environment: {environment}")


config = get_config()
