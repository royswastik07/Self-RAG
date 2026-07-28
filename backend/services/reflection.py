import json
from groq import AsyncGroq
from typing import Dict, Any
from core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

class ReflectionService:
    async def evaluate_and_reflect(self, query: str, context: str, draft_answer: str) -> Dict[str, Any]:
        """
        Uses an LLM to reflect on the retrieved context and draft answer.
        Returns JSON determining if it's supported, confidence, and if re-retrieval is needed.
        """
        prompt = f"""
You are an advanced Self-RAG reflection system. Your job is to evaluate if a generated answer is fully supported by the retrieved context.

User Query: {query}

Retrieved Context:
{context}

Draft Answer:
{draft_answer}

Evaluate the following:
1. Is the draft answer fully supported by the context without hallucinating?
2. If it is NOT supported, or if the context lacks information to answer the query, suggest a new search query to retrieve better information.

Return ONLY a valid JSON object with the following schema, and no other text or markdown formatting:
{{
  "supported": bool, // true if fully supported, false otherwise
  "confidence": float, // 0.0 to 1.0 confidence score
  "retrieve_again": bool, // true if we should try searching again with a new query, false if we should stop
  "new_query": str, // suggested new search query if retrieve_again is true, else ""
  "reason": str // brief explanation of your decision
}}
"""

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise JSON-only outputting evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE,
            response_format={"type": "json_object"}
        )

        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except json.JSONDecodeError:
            # Fallback in case of failure
            return {
                "supported": False,
                "confidence": 0.0,
                "retrieve_again": False,
                "new_query": "",
                "reason": "Failed to parse reflection output."
            }

reflection_service = ReflectionService()
