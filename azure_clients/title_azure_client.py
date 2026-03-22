from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from utils.logger import get_logger

logger = get_logger()
load_dotenv()

def get_client():
    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION")
        )
        logger.info("AzureOpenAI client created successfully.")
    except Exception as e:
        logger.error(f"Error creating AzureOpenAI client: {e}")
        client = None
    return client

