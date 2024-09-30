from typing import List, Optional

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
    chat_model = ChatOpenAI(temperature=.8, openai_api_key=config.OPENAI_API_KEY, model="gpt-4o")
    return chat_model

def get_fake_chat_model():
    fake_responses: List[BaseMessage] = [BaseMessage(content="This is a fake response.", type="text")]
    chat_model = FakeMessagesListChatModel(responses=fake_responses)
    return chat_model


def setup_chat_model(custom_prompt: Optional[str] = None,llm_model:Optional[str] = 'fake'):
    if llm_model == 'openai':
        model_setup_function = get_openai_chat_model
    elif llm_model == 'fake':
        model_setup_function = get_fake_chat_model
    elif llm_model == 'lmstudio':
        model_setup_function = get_lmstudio_model
    else:
        raise ValueError(f"Unsupported chat model provider: {llm_model}")

    chat_model = model_setup_function()

    # Use the custom prompt if provided, otherwise use the default from config
    prompt_template = custom_prompt+" {text}" if custom_prompt else config.TEMPLATE
    prompt = ChatPromptTemplate.from_template(prompt_template)

    return prompt | chat_model | StrOutputParser()
def get_openai_embedding_model():
    return OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)

def get_lmstudio_model():
    client = ChatOpenAI(base_url=config.LOCAL_LLM_URL, api_key="not-needed")
    return client

def get_fake_embedding_model():
    return FakeEmbeddings(size=1536)

def setup_embedding_model(llm_model:Optional[str] = 'fake'):
    if llm_model == 'openai':
        model_setup_function = get_openai_embedding_model
    elif llm_model == 'fake':
        model_setup_function = get_fake_embedding_model
    elif llm_model == 'lmstudio':
        model_setup_function = get_openai_embedding_model
    else:
        raise ValueError(f"Unsupported embedding model provider: {config.EMBEDDING_MODEL_PROVIDER}")
    embedding_model = model_setup_function()
    return embedding_model