from groq import AsyncGroq
from core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

class GenerationService:
    async def generate_answer(self, query: str, context: str) -> str:
        """
        Generates an answer based ONLY on the provided context.
        """
        prompt = f"""
You are an expert assistant. Answer the user's question based ONLY on the provided context.
If the context does not contain sufficient information to answer the question, say exactly:
"I could not find sufficient evidence in the uploaded documents."

Context:
{context}

Question: {query}
"""
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise, grounded assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE
        )
        return response.choices[0].message.content.strip()

generation_service = GenerationService()
