from app.ai.llm_client import generate_json

GAP_PROMPT = """Analyze common learning gaps and misconceptions for {subject} - {topic} ({grade}).

Concepts and Misconceptions:
{concepts}

Learning Objectives:
{objectives}

Return ONLY valid JSON:
{{
  "learning_gaps": [
    {{
      "gap_id": "GAP-1",
      "description": "...",
      "severity": "low|medium|high",
      "diagnostic_question": "...",
      "expected_wrong_answer": "...",
      "remedial_action": "...",
      "related_concepts": ["..."]
    }}
  ]
}}
"""

class GapAnalyzerService:
    async def process(self, knowledge: dict, config: dict) -> dict:
        concepts_text = ""
        for c in knowledge.get("common_misconceptions", []):
            concepts_text += f"- Misconception: {c.get('misconception')} → Truth: {c.get('correct_understanding')}\n"
        prompt = GAP_PROMPT.format(
            subject=config.get("subject", "General"), topic=config.get("topic", "General"),
            grade=config.get("grade", "Unknown"),
            concepts=concepts_text[:2000] or "Standard educational concepts",
            objectives="\n".join(f"- {o}" for o in knowledge.get("learning_objectives", []))
        )
        return await generate_json(prompt)
