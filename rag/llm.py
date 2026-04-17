import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    return ChatGroq(
        temperature=0,
        model="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


def get_llm_response(prompt: str) -> str:
    llm = get_llm()

    try:
        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"