import json
from datetime import datetime, timezone
from pathlib import Path
from app.core.config import settings
from app.core.logging_config import logger

class PublisherService:
    async def process(self, state: dict) -> dict:
        tkp = self._assemble_tkp(state)
        output_dir = Path(settings.OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"tkp_{state['job_id']}.json"
        filepath = output_dir / filename
        filepath.write_text(json.dumps(tkp, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("tkp_published", job_id=state["job_id"], path=str(filepath))
        return {"tkp_path": str(filepath), "tkp": tkp}

    def _assemble_tkp(self, state: dict) -> dict:
        md = state.get("metadata", {})
        tp = state.get("teaching_plan", {})
        ct = state.get("content", {})
        ac = state.get("activities", {})
        asm = state.get("assessments", {})
        ga = state.get("gaps", {})
        vr = state.get("validation_report", {})
        if ct.get("periods"):
            for period in tp.get("periods", []):
                pn = period["period_number"]
                matching = [p for p in ct["periods"] if p.get("period_number") == pn]
                if matching:
                    period.update(matching[0])
                if ac.get("period_activities", {}).get(pn):
                    period["classroom_activities"] = ac["period_activities"][pn]
        return {
            "metadata": {
                "document_title": state.get("file_path", "").split("\\")[-1].split("/")[-1],
                "subject": md.get("subject", "General"),
                "grade": md.get("grade", "Unknown"),
                "difficulty": md.get("difficulty", "intermediate"),
                "topic": md.get("topic", "General"),
                "chapter": md.get("chapter", ""),
                "category": md.get("category", "General"),
                "language": md.get("language", "English"),
                "board_alignment": md.get("board_alignment", "General"),
                "total_periods": len(tp.get("periods", [])),
                "period_duration_minutes": tp.get("periods", [{}])[0].get("duration_minutes", 40) if tp.get("periods") else 40,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "knowledge_base": state.get("knowledge", {}),
            "teaching_plan": tp,
            "assessments": asm,
            "learning_gaps": ga.get("learning_gaps", []),
            "validation_report": vr,
        }
