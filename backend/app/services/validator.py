from app.core.logging_config import logger

class ValidatorService:
    async def process(self, state: dict) -> dict:
        report = {
            "schema_valid": True,
            "completeness_score": 1.0,
            "missing_elements": [],
            "consistency_issues": [],
            "hallucination_flags": [],
        }
        tkp = state.get("tkp", {})
        if not tkp.get("knowledge_base"):
            report["missing_elements"].append("knowledge_base")
            report["completeness_score"] -= 0.2
        kb = tkp.get("knowledge_base", {})
        if not kb.get("learning_objectives"):
            report["missing_elements"].append("learning_objectives")
            report["completeness_score"] -= 0.1
        if not kb.get("concepts"):
            report["missing_elements"].append("concepts")
            report["completeness_score"] -= 0.15
        tp = tkp.get("teaching_plan", {})
        periods = tp.get("periods", [])
        if not periods:
            report["missing_elements"].append("teaching_plan.periods")
            report["completeness_score"] -= 0.2
        for i, p in enumerate(periods):
            if not p.get("learning_objectives"):
                report["consistency_issues"].append(f"Period {i+1} missing learning objectives")
                report["completeness_score"] -= 0.05
        if not tkp.get("assessments"):
            report["missing_elements"].append("assessments")
            report["completeness_score"] -= 0.15
        if not tkp.get("learning_gaps"):
            report["missing_elements"].append("learning_gaps")
            report["completeness_score"] -= 0.1
        report["completeness_score"] = max(0.0, round(report["completeness_score"], 2))
        report["schema_valid"] = report["completeness_score"] >= 0.5
        logger.info("validation_complete", score=report["completeness_score"], issues=len(report["consistency_issues"]))
        return report
