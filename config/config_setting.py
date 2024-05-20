import os
import json
from functools import lru_cache
from pydantic import  ConfigDict
from typing import Optional, Dict
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    """Base Configuration Class"""
    APP_NAME: str = "Kafka Consumer with vector data base additions"
    TITLE: str = "Kafka Consumer Vector DB ingestors"
    DESCRIPTION: str = "Service consuming Kafka topics and adding to vector db."
    GITHUB_TOKEN: Optional[str]
    BROKERS: Optional[str] = None
    INPUT_TOPIC: Optional[str] = None
    OUTPUT_TOPIC: Optional[str] = None
    CONSUMER_CONFIG: Optional[Dict[str, str]] = None
    PRODUCER_CONFIG: Optional[Dict[str, str]] = None
    MODEL_PROVIDER: Optional[str] = "fake"
    TEMPLATE: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    PROCESSED_TOPIC: Optional[str] = None

    model_config = ConfigDict(env_file=".env", env_file_encoding='utf-8')

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
