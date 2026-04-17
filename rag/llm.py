import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()


def get_llm():
    return ChatGroq(
        temperature=0,
        model_name="llama-3.1-8b-instant",
        groq_api_key=os.getenv("GROQ_API_KEY")
    )


def get_llm_response(prompt: str) -> str:
    """Invoke the LLM with a pre-built prompt string."""
    llm = get_llm()

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()

        if not answer or "no information" in answer.lower():
            return "No information available"

        return answer

    except Exception as e:
        return f"Error generating response: {str(e)}"