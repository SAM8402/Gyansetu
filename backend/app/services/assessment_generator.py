from app.ai.llm_client import generate_json

ASSESSMENT_PROMPT = """Generate comprehensive assessments for {subject} - {topic} ({grade}, {difficulty}).

Learning Objectives: {objectives}
Concepts: {concepts}
Language: {language}

Return ONLY valid JSON:
{{
  "mcqs": [{{"question": "...", "options": ["A","B","C","D"], "correct_answer": "A", "explanation": "...", "difficulty": "easy|medium|hard", "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create"}}],
  "short_answers": [{{"question": "...", "model_answer": "...", "marks": 2, "rubric": "..."}}],
  "long_answers": [{{"question": "...", "model_answer": "...", "marks": 5, "rubric": "..."}}],
  "numerical_problems": [{{"question": "...", "solution": "...", "answer": "...", "marks": 3}}]
}}

Generate at least 10 MCQs, 5 short answers, 3 long answers, and 2-5 numerical problems (if STEM).
Generate ALL content in {language}.
"""

class AssessmentGeneratorService:
    async def process(self, knowledge: dict, metadata: dict, config: dict) -> dict:
        language = config.get("target_language", metadata.get("language", "English"))
        prompt = ASSESSMENT_PROMPT.format(
            subject=metadata.get("subject", "General"), topic=metadata.get("topic", "General"),
            grade=metadata.get("grade", "Unknown"), difficulty=metadata.get("difficulty", "intermediate"),
            language=language,
            objectives="\n".join(f"- {o}" for o in knowledge.get("learning_objectives", [])),
            concepts="\n".join(f"- {c['name']}: {c['definition'][:100]}" for c in knowledge.get("concepts", []))
        )
        return await generate_json(prompt)
