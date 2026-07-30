import asyncio
from app.ai.llm_client import generate_json

CONTENT_PROMPT = """Generate detailed classroom teaching content for period {period_number}: "{title}".
Duration: {duration} minutes
Subject: {subject} | Topic: {topic} | Grade: {grade} | Language: {language}

Learning Objectives: {objectives}
Key Concepts: {concepts}

Return ONLY valid JSON with these fields:
{{
  "entry_ticket": {{"question": "...", "purpose": "..."}},
  "teacher_script": "...",
  "blackboard_notes": "...",
  "checkpoint_questions": [{{"question": "...", "expected_answer": "..."}}],
  "exit_ticket": {{"question": "...", "expected_answer": "..."}},
  "homework": {{"description": "...", "questions": ["..."]}},
  "mentor_moment": {{"anecdote": "...", "connection_to_topic": "..."}}
}}

Generate ALL output in {language}.
"""

class ContentGeneratorService:
    async def process(self, teaching_plan: dict, knowledge: dict, metadata: dict, config: dict) -> dict:
        periods = teaching_plan.get("periods", [])
        language = config.get("target_language", metadata.get("language", "English"))

        async def generate_period_content(period: dict) -> dict:
            prompt = CONTENT_PROMPT.format(
                period_number=period["period_number"], title=period.get("title", ""),
                duration=period.get("duration_minutes", 40), subject=metadata.get("subject", "General"),
                topic=metadata.get("topic", "General"), grade=metadata.get("grade", "Unknown"),
                language=language,
                objectives="; ".join(period.get("learning_objectives", [])),
                concepts="; ".join(period.get("key_concepts", []))
            )
            return await generate_json(prompt)

        results = await asyncio.gather(*[generate_period_content(p) for p in periods])
        return {"periods": [{**p, **r} for p, r in zip(periods, results)]}
