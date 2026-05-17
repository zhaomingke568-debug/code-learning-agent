"""
Report API routes.
"""
from fastapi import APIRouter, HTTPException

from backend.models.schemas import ReportResponse
from backend.agents.graph_runner import graph_runner
from backend.agents.state_adapter import StateAdapter

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/{threadId}", response_model=ReportResponse)
async def get_report(threadId: str):
    """Get learning progress report."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    state_adapter = StateAdapter()
    report_data = state_adapter.extract_report(state)

    return ReportResponse(
        topic=report_data["topic"],
        depthLevel=report_data["depthLevel"],
        assessmentResult=report_data["assessmentResult"],
        completedMilestones=report_data["completedMilestones"],
        codeExecutionResult=report_data["codeExecutionResult"],
        weakPoints=report_data["weakPoints"],
        strongPoints=report_data["strongPoints"],
        learningHistory=report_data["learningHistory"]
    )