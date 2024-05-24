from typing import List

from langchain.chains.base import Chain
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.chat_models.fake import FakeMessagesListChatModel
from langchain_core.messages import BaseMessage
from config.config_setting import config
from icecream import ic

def get_openai_chat_model():
    chat_model = ChatOpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model="gpt-3.5-turbo")
    return chat_model

def get_fake_chat_model():
    fake_responses: List[BaseMessage] = [BaseMessage(content="This is a fake response.", type="text")]
    chat_model = FakeMessagesListChatModel(responses=fake_responses)
    return chat_model

def setup_chat_model():
    if config.MODEL_PROVIDER == 'openai':
        ic("open ai model is being used")
        model_setup_function = get_openai_chat_model
    elif config.MODEL_PROVIDER == 'fake':
        ic("Fake model is being used")
        model_setup_function = get_fake_chat_model
    else:
        raise ValueError(f"Unsupported chat model provider: {config.MODEL_PROVIDER}")
    chat_model = model_setup_function()
    prompt = ChatPromptTemplate.from_template(config.TEMPLATE)
    return prompt | chat_model | StrOutputParser()
def get_openai_embedding_model():
    return OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)

def get_fake_embedding_model():
    return FakeEmbeddings(size=1536)

def setup_embedding_model():
    if config.MODEL_PROVIDER == 'openai':
        ic("OpenAI embedding model is being used")
        model_setup_function = get_openai_embedding_model
    elif config.MODEL_PROVIDER == 'fake':
        ic("Fake embedding model is being used")
        model_setup_function = get_fake_embedding_model
    else:
        raise ValueError(f"Unsupported embedding model provider: {config.EMBEDDING_MODEL_PROVIDER}")
    embedding_model = model_setup_function()
    return embedding_model