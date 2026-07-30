import asyncio
from app.ai.llm_client import generate_json

ACTIVITY_PROMPT = """Design 1-2 classroom activities for period {period_number}: "{title}".
Subject: {subject} | Topic: {topic} | Duration: {duration} min | Language: {language}

Return ONLY valid JSON:
{{
  "activities": [
    {{
      "type": "Demonstration|Role Play|Experiment|Group Discussion|Think-Pair-Share|Quiz Game",
      "title": "...",
      "duration_minutes": 10,
      "materials_needed": ["..."],
      "teacher_instructions": "...",
      "student_instructions": "...",
      "success_criteria": "..."
    }}
  ]
}}

Generate in {language}.
"""

class ActivityGeneratorService:
    async def process(self, teaching_plan: dict, knowledge: dict, content: dict, config: dict) -> dict:
        periods = teaching_plan.get("periods", [])
        language = config.get("target_language", "English")

        async def generate_activities(period: dict) -> dict:
            prompt = ACTIVITY_PROMPT.format(
                period_number=period["period_number"], title=period.get("title", ""),
                subject="General", topic="General", duration=period.get("duration_minutes", 40),
                language=language
            )
            return await generate_json(prompt)

        results = await asyncio.gather(*[generate_activities(p) for p in periods])
        activities_by_period = {}
        for p, r in zip(periods, results):
            activities_by_period[p["period_number"]] = r.get("activities", [])
        return {"period_activities": activities_by_period}
