from app.ai.llm_client import generate_json

CLASSIFICATION_PROMPT = """Analyze the following educational document and classify it. Return ONLY valid JSON:
{
  "subject": "...",
  "grade": "...",
  "difficulty": "beginner|intermediate|advanced",
  "topic": "...",
  "chapter": "...",
  "category": "STEM|Humanities|Arts|Commerce",
  "language": "...",
  "board_alignment": "CBSE|ICSE|Common Core|General"
}

Document preview:
{text}
"""

class EduClassifierService:
    async def process(self, doc_data: dict, config: dict) -> dict:
        text = doc_data.get("raw_text", "")[:2000]
        headings = "\n".join(s["heading"] for s in doc_data.get("sections", [])[:20])
        prompt = CLASSIFICATION_PROMPT.format(text=text[:1500] + "\n\nHeadings:\n" + headings[:500])
        result = await generate_json(prompt)
        if config.get("target_language"):
            result["language"] = config["target_language"]
        if config.get("board_alignment"):
            result["board_alignment"] = config["board_alignment"]
        return result
