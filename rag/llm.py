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


def get_llm_response(query, docs):

    llm = get_llm()

    # Build context
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are an enterprise AI assistant.

Answer ONLY from the provided context.
Do NOT make assumptions.
If the answer is not in the context, say: "No information available".

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)

    return response.content