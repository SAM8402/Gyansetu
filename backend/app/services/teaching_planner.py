from app.ai.llm_client import generate_json

PLANNER_PROMPT = """Create a multi-period teaching plan based on the following knowledge. Return ONLY valid JSON:
{{
  "periods": [
    {{
      "period_number": 1,
      "title": "...",
      "duration_minutes": {duration},
      "learning_objectives": ["..."],
      "key_concepts": ["..."],
      "activities_summary": "...",
      "assessment_strategy": "..."
    }}
  ]
}}

Knowledge:
- Subject: {subject}
- Topic: {topic}
- Grade: {grade}
- Difficulty: {difficulty}
- Board: {board}
- Language: {language}
- Teaching Style: {teaching_style}
- Number of periods: {num_periods}

Concepts:
{concepts}

Learning Objectives:
{objectives}

Prerequisites:
{prereqs}
"""

class TeachingPlannerService:
    async def process(self, knowledge: dict, metadata: dict, config: dict) -> dict:
        duration = config.get("period_duration", 40)
        num_periods = config.get("num_periods", 0) or max(3, len(knowledge.get("concepts", [])) // 2 + 1)
        teaching_style = config.get("teaching_style", metadata.get("teaching_style", "Interactive & Activity-Driven"))
        concepts_text = "\n".join(f"- {c['name']}: {c['definition'][:100]}" for c in knowledge.get("concepts", []))
        objectives_text = "\n".join(f"- {o}" for o in knowledge.get("learning_objectives", []))
        prereqs_text = "\n".join(f"- {p}" for p in knowledge.get("prerequisites", []))
        prompt = PLANNER_PROMPT.format(
            duration=duration, subject=metadata.get("subject", "General"), topic=metadata.get("topic", "General"),
            grade=metadata.get("grade", "Unknown"), difficulty=metadata.get("difficulty", "intermediate"),
            board=metadata.get("board_alignment", "General"), language=metadata.get("language", "English"),
            teaching_style=teaching_style,
            num_periods=num_periods, concepts=concepts_text[:2000], objectives=objectives_text[:1000],
            prereqs=prereqs_text[:500]
        )
        result = await generate_json(prompt)
        for p in result.get("periods", []):
            p["duration_minutes"] = duration
        return result
