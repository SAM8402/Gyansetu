import asyncio
from datetime import datetime, timezone
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from app.core.logging_config import logger

from app.services.document_intel import DocumentIntelService
from app.services.edu_classifier import EduClassifierService
from app.services.knowledge_extractor import KnowledgeExtractorService
from app.services.teaching_planner import TeachingPlannerService
from app.services.content_generator import ContentGeneratorService
from app.services.activity_generator import ActivityGeneratorService
from app.services.assessment_generator import AssessmentGeneratorService
from app.services.gap_analyzer import GapAnalyzerService
from app.services.validator import ValidatorService
from app.services.publisher import PublisherService


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
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Document Intelligence", 1, 10, 10, "Extracting text & layout...")
    from app.services.document_intel import DocumentIntelService
    result = await DocumentIntelService().process(state["file_path"])
    return {"doc_data": result, "current_stage": 1}


async def educational_classification_node(state: PipelineState) -> dict:
    """Classify the document by subject, audience, and educational level."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Educational Classification", 2, 10, 20, "Classifying subject & grade...")
    from app.services.edu_classifier import EduClassifierService
    result = await EduClassifierService().process(state["doc_data"], state["config"])
    return {"metadata": result, "current_stage": 2}


async def knowledge_extraction_node(state: PipelineState) -> dict:
    """Extract structured knowledge graph from the document content."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Knowledge Extraction", 3, 10, 30, "Extracting key concepts...")
    from app.services.knowledge_extractor import KnowledgeExtractorService
    result = await KnowledgeExtractorService().process(state["doc_data"], state["metadata"])
    return {"knowledge": result, "current_stage": 3}


async def teaching_planning_node(state: PipelineState) -> dict:
    """Generate a high-level teaching plan based on extracted knowledge."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Teaching Planning", 4, 10, 40, "Building period lesson plan...")
    from app.services.teaching_planner import TeachingPlannerService
    result = await TeachingPlannerService().process(
        state["knowledge"], state["metadata"], state["config"]
    )
    return {"teaching_plan": result, "current_stage": 4}


async def content_generation_node(state: PipelineState) -> dict:
    """Produce lecture-ready content aligned with the teaching plan."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Content Generation", 5, 10, 50, "Generating lecture notes...")
    from app.services.content_generator import ContentGeneratorService
    result = await ContentGeneratorService().process(
        state["teaching_plan"],
        state["knowledge"],
        state["metadata"],
        state["config"],
    )
    return {"content": result, "current_stage": 5}


async def activity_generation_node(state: PipelineState) -> dict:
    """Create interactive classroom activities and exercises."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Activity Generation", 6, 10, 60, "Generating classroom activities...")
    from app.services.activity_generator import ActivityGeneratorService
    result = await ActivityGeneratorService().process(
        state["teaching_plan"],
        state["knowledge"],
        state["content"],
        state["config"],
    )
    return {"activities": result, "current_stage": 6}


async def assessment_generation_node(state: PipelineState) -> dict:
    """Build assessments (quizzes, assignments) from knowledge and metadata."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Assessment Generation", 7, 10, 70, "Creating quizzes & assignments...")
    from app.services.assessment_generator import AssessmentGeneratorService
    result = await AssessmentGeneratorService().process(
        state["knowledge"], state["metadata"], state["config"]
    )
    return {"assessments": result, "current_stage": 7}


async def gap_analysis_node(state: PipelineState) -> dict:
    """Identify knowledge gaps and missing prerequisites."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Gap Analysis", 8, 10, 80, "Analyzing prerequisite gaps...")
    from app.services.gap_analyzer import GapAnalyzerService
    result = await GapAnalyzerService().process(
        state["knowledge"],
        {**state["config"], **state.get("metadata", {})},
    )
    return {"gaps": result, "current_stage": 8}


async def parallel_generation_node(state: PipelineState) -> dict:
    """Execute Content, Assessment, and Gap Analysis in parallel for maximum performance."""
    from app.services.content_generator import ContentGeneratorService
    from app.services.activity_generator import ActivityGeneratorService
    from app.services.assessment_generator import AssessmentGeneratorService
    from app.services.gap_analyzer import GapAnalyzerService

    tp = state["teaching_plan"]
    kn = state["knowledge"]
    md = state.get("metadata", {})
    cfg = state["config"]

    # Run Content Gen, Assessment Gen, and Gap Analysis concurrently
    c_task = ContentGeneratorService().process(tp, kn, md, cfg)
    asm_task = AssessmentGeneratorService().process(kn, md, cfg)
    gap_task = GapAnalyzerService().process(kn, {**cfg, **md})

    content, assessments, gaps = await asyncio.gather(c_task, asm_task, gap_task)
    activities = await ActivityGeneratorService().process(tp, kn, content, cfg)

    return {
        "content": content,
        "activities": activities,
        "assessments": assessments,
        "gaps": gaps,
        "current_stage": 8,
    }


async def tkp_assembly_node(state: PipelineState) -> dict:
    """Assemble all individual stage outputs into the final TKP structure."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Validation & Assembly", 9, 10, 90, "Assembling package...")

    md = state.get("metadata", {})
    tp = state.get("teaching_plan", {})
    ct = state.get("content", {})
    ac = state.get("activities", {})
    asm = state.get("assessments", {})
    ga = state.get("gaps", {})

    if ct.get("periods"):
        for period in tp.get("periods", []):
            pn = period["period_number"]
            matching = [p for p in ct["periods"] if p.get("period_number") == pn]
            if matching:
                period.update(matching[0])
            if ac.get("period_activities", {}).get(pn):
                period["classroom_activities"] = ac["period_activities"][pn]

    return {
        "tkp": {
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
            "validation_report": {},
        },
        "current_stage": 9,
    }


async def validation_node(state: PipelineState) -> dict:
    """Validate the entire pipeline output for consistency and completeness."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Validation", 9, 10, 95, "Validating completeness...")
    from app.services.validator import ValidatorService
    result = await ValidatorService().process(state)
    return {"validation_report": result, "current_stage": 10}


async def publishing_node(state: PipelineState) -> dict:
    """Persist the final output and mark the pipeline as complete."""
    if state.get("job_id"):
        from app.services.cache_service import cache_service
        await cache_service.publish_progress(state["job_id"], "Publishing", 10, 10, 100, "Publishing final package...")
    from app.services.publisher import PublisherService
    result = await PublisherService().process(state)
    return {"result": result, "current_stage": 11}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def build_pipeline() -> StateGraph:
    """Assemble and compile the LangGraph pipeline.

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
    graph.add_node("tkp_assembly", tkp_assembly_node)
    graph.add_node("validation", validation_node)
    graph.add_node("publishing", publishing_node)

    # Entry point
    graph.set_entry_point("document_intelligence")

    # Sequential edges
    graph.add_edge("document_intelligence", "educational_classification")
    graph.add_edge("educational_classification", "knowledge_extraction")
    graph.add_edge("knowledge_extraction", "teaching_planning")
    graph.add_edge("teaching_planning", "content_generation")
    graph.add_edge("content_generation", "activity_generation")
    graph.add_edge("activity_generation", "assessment_generation")
    graph.add_edge("assessment_generation", "gap_analysis")
    graph.add_edge("gap_analysis", "tkp_assembly")
    graph.add_edge("tkp_assembly", "validation")
    graph.add_edge("validation", "publishing")
    graph.add_edge("publishing", END)

    return graph.compile()
