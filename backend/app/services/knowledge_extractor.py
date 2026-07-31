from app.ai.llm_client import generate_json
from app.ai.embeddings import chunk_document, HybridRetriever
from app.core.logging_config import logger

EXTRACTION_PROMPT = """Based on the following educational document content, extract structured knowledge. Return ONLY valid JSON:
{{
  "learning_objectives": ["..."],
  "prerequisites": ["..."],
  "concepts": [{{"name": "...", "definition": "...", "explanation": "...", "examples": ["..."], "source_reference": "..."}}],
  "definitions": [{{"term": "...", "definition": "..."}}],
  "formulae": [{{"formula": "...", "description": "..."}}],
  "keywords": ["..."],
  "applications": ["..."],
  "common_misconceptions": [{{"misconception": "...", "correct_understanding": "...", "why_students_think_this": "..."}}]
}}

Document content:
{context}

Focus on educational concepts relevant to: {subject} - {topic}
"""

import asyncio

class KnowledgeExtractorService:
    async def process(self, doc_data: dict, metadata: dict) -> dict:
        text = doc_data.get("raw_text", "")
        relevant = await asyncio.to_thread(self._retrieve_sync, text, doc_data, metadata)
        context = "\n\n".join(d.page_content for d in relevant)
        prompt = EXTRACTION_PROMPT.format(context=context[:6000], subject=metadata.get("subject", "General"), topic=metadata.get("topic", "General"))
        result = await generate_json(prompt)
        return result

    def _retrieve_sync(self, text: str, doc_data: dict, metadata: dict):
        docs = chunk_document(text, {"source": doc_data.get("metadata", {}).get("file_type", "unknown")})
        retriever = HybridRetriever(docs)
        return retriever.hybrid_search(f"{metadata.get('subject', '')} {metadata.get('topic', '')} educational concepts", k=8)
