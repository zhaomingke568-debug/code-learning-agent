"""
Assessment API routes.
"""
from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    AssessmentSubmitRequest, AssessmentResponse
)
from backend.agents.graph_runner import graph_runner
from backend.agents.state_adapter import StateAdapter

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.post("/submit", response_model=AssessmentResponse)
async def submit_assessment(req: AssessmentSubmitRequest):
    """Submit assessment answers."""
    # Provide assessment answers to the graph
    result = await graph_runner.provide_input(
        thread_id=req.threadId,
        input_type="assessment",
        value=req.answers
    )

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    state_adapter = StateAdapter()
    return AssessmentResponse(
        assessmentResult=result.get("assessment_result", {}),
        learningPath=state_adapter.extract_learning_path(result) or {},
        nextStep=result.get("next_step", "")
    )


@router.get("/questions/{threadId}")
async def get_assessment_questions(threadId: str):
    """Get current assessment questions for a thread."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # The assessment questions would be in the state
    # This endpoint is mainly for the initial assessment flow
    return {
        "questions": state.get("assessmentQuestions", []),
        "topic": state.get("topic", ""),
        "depthLevel": state.get("depthLevel", "进阶")
    }