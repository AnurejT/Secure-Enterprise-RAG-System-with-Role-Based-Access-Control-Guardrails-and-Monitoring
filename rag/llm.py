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

    # 🔥 Combine retrieved documents
    context = "\n\n".join([doc.page_content for doc in docs])

    # 🔥 Strong and clear prompt
    prompt = f"""
You are a strict enterprise AI assistant.

Rules:
- Answer ONLY using the provided context.
- Do NOT use outside knowledge.
- If the answer is not clearly present, say EXACTLY: "No information available".
- Be precise and concise.

Context:
{context}

Question:
{query}

Answer:
"""

    try:
        response = llm.invoke(prompt)
        answer = response.content.strip()

        # 🔥 Safety fallback (very important)
        if not answer or "no information" in answer.lower():
            return "No information available"

        return answer

    except Exception as e:
        return f"Error generating response: {str(e)}"