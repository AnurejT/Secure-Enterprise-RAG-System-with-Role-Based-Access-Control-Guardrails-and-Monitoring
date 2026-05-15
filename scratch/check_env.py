import os
from dotenv import load_dotenv
from backend.core import config

load_dotenv()
print(f"OS GROQ_API_KEY: {os.getenv('GROQ_API_KEY')}")
print(f"CONFIG GROQ_API_KEY: {config.GROQ_API_KEY}")
