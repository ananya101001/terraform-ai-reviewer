from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm(temperature: float = 0.1):
    return ChatOpenAI(
        model=os.getenv("LLM_MODEL", "qwen3-coder"),
        api_key=os.getenv("UNCLOSEAI_API_KEY"),
        base_url=os.getenv("UNCLOSEAI_BASE_URL", "https://api.uncloseai.com/v1"),
        temperature=temperature,
    )