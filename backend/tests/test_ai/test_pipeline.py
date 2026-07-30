import pytest
from unittest.mock import AsyncMock, patch

from app.ai.pipeline import create_initial_state, build_pipeline


class TestCreateInitialState:
    def test_returns_all_keys(self):
        state = create_initial_state()
        expected_keys = {
            "job_id", "file_path", "config", "doc_data", "metadata",
            "knowledge", "teaching_plan", "content", "activities",
            "assessments", "gaps", "tkp", "validation_report", "result",
            "current_stage", "error",
        }
        assert set(state.keys()) == expected_keys

    def test_defaults_are_sensible(self):
        state = create_initial_state()
        assert state["current_stage"] == 0
        assert state["error"] is None
        assert state["job_id"] == ""
        assert all(state[k] == {} for k in ["config", "doc_data", "metadata", "knowledge", "teaching_plan", "content", "activities", "assessments", "gaps", "tkp", "validation_report", "result"])


class TestBuildPipeline:
    def test_returns_compiled_graph(self):
        pipeline = build_pipeline()
        assert pipeline is not None

    def test_graph_has_all_nodes(self):
        graph = build_pipeline()
        compiled_nodes = set(graph.get_graph().nodes)
        expected = {
            "__start__", "__end__",
            "document_intelligence", "educational_classification",
            "knowledge_extraction", "teaching_planning",
            "content_generation", "activity_generation",
            "assessment_generation", "gap_analysis",
            "tkp_assembly", "validation", "publishing",
        }
        assert compiled_nodes == expected


@pytest.mark.asyncio
async def test_full_pipeline_runs():
    """Integration test: mock all service dependencies and run the pipeline."""
    mock_patches = [
        patch("app.services.document_intel.DocumentIntelService", return_value=AsyncMock(
            process=AsyncMock(return_value={"text": "doc content"})
        )),
        patch("app.services.edu_classifier.EduClassifierService", return_value=AsyncMock(
            process=AsyncMock(return_value={"subject": "math", "level": "high-school"})
        )),
        patch("app.services.knowledge_extractor.KnowledgeExtractorService", return_value=AsyncMock(
            process=AsyncMock(return_value={"concepts": ["algebra"]})
        )),
        patch("app.services.teaching_planner.TeachingPlannerService", return_value=AsyncMock(
            process=AsyncMock(return_value={"plan": "teach algebra"})
        )),
        patch("app.services.content_generator.ContentGeneratorService", return_value=AsyncMock(
            process=AsyncMock(return_value={"slides": ["intro"]})
        )),
        patch("app.services.activity_generator.ActivityGeneratorService", return_value=AsyncMock(
            process=AsyncMock(return_value={"exercises": ["problem set"]})
        )),
        patch("app.services.assessment_generator.AssessmentGeneratorService", return_value=AsyncMock(
            process=AsyncMock(return_value={"quiz": ["q1"]})
        )),
        patch("app.services.gap_analyzer.GapAnalyzerService", return_value=AsyncMock(
            process=AsyncMock(return_value={"missing": ["prerequisites"]})
        )),
        patch("app.services.validator.ValidatorService", return_value=AsyncMock(
            process=AsyncMock(return_value={"score": 0.85})
        )),
        patch("app.services.publisher.PublisherService", return_value=AsyncMock(
            process=AsyncMock(return_value={"tkp_path": "/tmp/tkp.json"})
        )),
    ]

    with _multi_patch(mock_patches):
        pipeline = build_pipeline()
        state = create_initial_state()
        state["job_id"] = "test-job"
        state["file_path"] = "/tmp/doc.pdf"
        state["config"] = {"audience": "students"}

        result = await pipeline.ainvoke(state)

        assert result["current_stage"] == 11
        assert result.get("tkp", {}).get("metadata", {}).get("subject") == "math"
        assert result["result"]["tkp_path"] == "/tmp/tkp.json"
        assert result["doc_data"]["text"] == "doc content"
        assert result["metadata"]["subject"] == "math"


def _multi_patch(patches):
    """Enter multiple patches and return a context manager."""
    import contextlib
    stack = contextlib.ExitStack()
    for p in patches:
        stack.enter_context(p)
    return stack
