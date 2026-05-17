"""
Feedback API routes.
"""
from fastapi import APIRouter, HTTPException

from backend.models.schemas import FeedbackSubmitRequest, FeedbackResponse
from backend.agents.graph_runner import graph_runner

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(req: FeedbackSubmitRequest):
    """Submit user feedback."""
    result = await graph_runner.provide_input(
        thread_id=req.threadId,
        input_type="feedback",
        value=req.feedback
    )

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    return FeedbackResponse(
        nextMilestoneIndex=result.get("milestoneIndex", result.get("current_milestone_index", 0)),
        nextStep=result.get("next_step", ""),
        isComplete=result.get("next_step") == "END"
    )