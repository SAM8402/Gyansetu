from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.core.logging_config import logger


class PipelineState(TypedDict):
    """Typed state dictionary flowing through the LangGraph pipeline.

    Each field holds the output of a corresponding pipeline stage.
    ``current_stage`` tracks progress and ``error`` captures failures.
    """

    job_id: str
    file_path: str
    config: dict
    doc_data: dict
    metadata: dict
    knowledge: dict
    teaching_plan: dict
    content: dict
    activities: dict
    assessments: dict
    gaps: dict
    tkp: dict
    validation_report: dict
    result: dict
    current_stage: int
    error: Optional[str]


def create_initial_state() -> PipelineState:
    """Return a blank pipeline state with sensible defaults."""
    return {
        "job_id": "",
        "file_path": "",
        "config": {},
        "doc_data": {},
        "metadata": {},
        "knowledge": {},
        "teaching_plan": {},
        "content": {},
        "activities": {},
        "assessments": {},
        "gaps": {},
        "tkp": {},
        "validation_report": {},
        "result": {},
        "current_stage": 0,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Pipeline node implementations (each delegates to its service layer)
# ---------------------------------------------------------------------------


async def document_intelligence_node(state: PipelineState) -> dict:
    """Extract raw text and structure from the uploaded document."""
    from app.services.document_intel import DocumentIntelService

    service = DocumentIntelService()
    result = await service.process(state["file_path"])
    return {"doc_data": result, "current_stage": 1}


async def educational_classification_node(state: PipelineState) -> dict:
    """Classify the document by subject, audience, and educational level."""
    from app.services.edu_classifier import EduClassifierService

    service = EduClassifierService()
    result = await service.process(state["doc_data"], state["config"])
    return {"metadata": result, "current_stage": 2}


async def knowledge_extraction_node(state: PipelineState) -> dict:
    """Extract structured knowledge graph from the document content."""
    from app.services.knowledge_extractor import KnowledgeExtractorService

    service = KnowledgeExtractorService()
    result = await service.process(state["doc_data"], state["metadata"])
    return {"knowledge": result, "current_stage": 3}


async def teaching_planning_node(state: PipelineState) -> dict:
    """Generate a high-level teaching plan based on extracted knowledge."""
    from app.services.teaching_planner import TeachingPlannerService

    service = TeachingPlannerService()
    result = await service.process(
        state["knowledge"], state["metadata"], state["config"]
    )
    return {"teaching_plan": result, "current_stage": 4}


async def content_generation_node(state: PipelineState) -> dict:
    """Produce lecture-ready content aligned with the teaching plan."""
    from app.services.content_generator import ContentGeneratorService

    service = ContentGeneratorService()
    result = await service.process(
        state["teaching_plan"],
        state["knowledge"],
        state["metadata"],
        state["config"],
    )
    return {"content": result, "current_stage": 5}


async def activity_generation_node(state: PipelineState) -> dict:
    """Create interactive classroom activities and exercises."""
    from app.services.activity_generator import ActivityGeneratorService

    service = ActivityGeneratorService()
    result = await service.process(
        state["teaching_plan"],
        state["knowledge"],
        state["content"],
        state["config"],
    )
    return {"activities": result, "current_stage": 6}


async def assessment_generation_node(state: PipelineState) -> dict:
    """Build assessments (quizzes, assignments) from knowledge and metadata."""
    from app.services.assessment_generator import AssessmentGeneratorService

    service = AssessmentGeneratorService()
    result = await service.process(
        state["knowledge"], state["metadata"], state["config"]
    )
    return {"assessments": result, "current_stage": 7}


async def gap_analysis_node(state: PipelineState) -> dict:
    """Identify knowledge gaps and missing prerequisites."""
    from app.services.gap_analyzer import GapAnalyzerService

    service = GapAnalyzerService()
    result = await service.process(state["knowledge"], state["config"])
    return {"gaps": result, "current_stage": 8}


async def validation_node(state: PipelineState) -> dict:
    """Validate the entire pipeline output for consistency and completeness."""
    from app.services.validator import ValidatorService

    service = ValidatorService()
    result = await service.process(state)
    return {"validation_report": result, "current_stage": 9}


async def publishing_node(state: PipelineState) -> dict:
    """Persist the final output and mark the pipeline as complete."""
    from app.services.publisher import PublisherService

    service = PublisherService()
    result = await service.process(state)
    return {"result": result, "current_stage": 10}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_pipeline() -> StateGraph:
    """Assemble and compile the LangGraph pipeline.

    The pipeline executes ten sequential stages:

        1. Document Intelligence
        2. Educational Classification
        3. Knowledge Extraction
        4. Teaching Planning
        5. Content Generation
        6. Activity Generation
        7. Assessment Generation
        8. Gap Analysis
        9. Validation
        10. Publishing

    Returns:
        A compiled ``StateGraph`` ready for invocation.
    """
    graph = StateGraph(PipelineState)

    # Register every node
    graph.add_node("document_intelligence", document_intelligence_node)
    graph.add_node("educational_classification", educational_classification_node)
    graph.add_node("knowledge_extraction", knowledge_extraction_node)
    graph.add_node("teaching_planning", teaching_planning_node)
    graph.add_node("content_generation", content_generation_node)
    graph.add_node("activity_generation", activity_generation_node)
    graph.add_node("assessment_generation", assessment_generation_node)
    graph.add_node("gap_analysis", gap_analysis_node)
    graph.add_node("validation", validation_node)
    graph.add_node("publishing", publishing_node)

    # Entry point
    graph.set_entry_point("document_intelligence")

    # Sequential edges (each node feeds the next)
    graph.add_edge("document_intelligence", "educational_classification")
    graph.add_edge("educational_classification", "knowledge_extraction")
    graph.add_edge("knowledge_extraction", "teaching_planning")
    graph.add_edge("teaching_planning", "content_generation")
    graph.add_edge("content_generation", "activity_generation")
    graph.add_edge("activity_generation", "assessment_generation")
    graph.add_edge("assessment_generation", "gap_analysis")
    graph.add_edge("gap_analysis", "validation")
    graph.add_edge("validation", "publishing")
    graph.add_edge("publishing", END)

    return graph.compile()
