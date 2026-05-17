"""
Session API routes.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.models.schemas import (
    StartSessionRequest, SessionResponse, StateResponse, RecoverResponse
)
from backend.agents.graph_runner import graph_runner

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionResponse)
async def start_session(req: StartSessionRequest):
    """Start a new learning session."""
    session_id, thread_id, status = await graph_runner.start_session(
        topic=req.topic,
        depth_level=req.depthLevel,
        existing_thread_id=req.threadId
    )
    return SessionResponse(
        sessionId=session_id,
        threadId=thread_id,
        status=status,
        createdAt=datetime.utcnow()
    )


@router.get("/{threadId}/state")
async def get_session_state(threadId: str):
    """Get current session state."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state


@router.post("/{threadId}/recover", response_model=RecoverResponse)
async def recover_session(threadId: str):
    """Recover an existing session."""
    state = await graph_runner.recover_session(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return RecoverResponse(
        state=state,
        resumedFrom=state.get("nextStep", "unknown")
    )