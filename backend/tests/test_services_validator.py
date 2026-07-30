import pytest

from app.services.validator import ValidatorService


@pytest.fixture
def service():
    return ValidatorService()


@pytest.mark.asyncio
class TestValidatorService:
    async def test_complete_tkp_with_learning_gaps(self, service):
        state = {
            "tkp": {
                "knowledge_base": {"learning_objectives": ["LO1"], "concepts": ["C1"]},
                "teaching_plan": {
                    "periods": [{"period_number": 1, "title": "Intro", "duration_minutes": 45, "learning_objectives": ["LO1"]}]
                },
                "assessments": {"mcqs": []},
                "learning_gaps": [{"gap": "none"}],
            }
        }
        report = await service.process(state)
        assert report["schema_valid"] is True
        assert report["completeness_score"] == 1.0
        assert report["missing_elements"] == []

    async def test_empty_tkp_low_score(self, service):
        state = {"tkp": {}}
        report = await service.process(state)
        assert report["schema_valid"] is False
        assert report["completeness_score"] < 0.5
        assert "knowledge_base" in report["missing_elements"]
        assert "assessments" in report["missing_elements"]
        assert "learning_gaps" in report["missing_elements"]

    async def test_missing_concepts_deducts(self, service):
        state = {
            "tkp": {
                "knowledge_base": {"learning_objectives": ["LO1"]},
                "teaching_plan": {"periods": [{"period_number": 1, "title": "X", "duration_minutes": 30}]},
                "assessments": {"mcqs": []},
                "learning_gaps": [{"g": "1"}],
            }
        }
        report = await service.process(state)
        assert "concepts" in report["missing_elements"]
        assert report["completeness_score"] <= 0.85

    async def test_period_missing_objectives_adds_consistency_issue(self, service):
        state = {
            "tkp": {
                "knowledge_base": {"learning_objectives": ["LO1"], "concepts": ["C1"]},
                "teaching_plan": {
                    "periods": [
                        {"period_number": 1, "title": "P1", "duration_minutes": 30},
                    ]
                },
                "assessments": {"mcqs": []},
                "learning_gaps": [{"g": "1"}],
            }
        }
        report = await service.process(state)
        assert len(report["consistency_issues"]) == 1
        assert "Period 1" in report["consistency_issues"][0]

    async def test_score_never_below_zero(self, service):
        state = {"tkp": {"knowledge_base": {}}}
        report = await service.process(state)
        assert report["completeness_score"] >= 0.0
