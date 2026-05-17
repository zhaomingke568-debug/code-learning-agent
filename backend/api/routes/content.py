"""
Content API routes - explanation and exercise retrieval.
"""
from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    ExplanationResponse, ExerciseResponse, LearningPathResponse
)
from backend.agents.graph_runner import graph_runner
from backend.agents.state_adapter import StateAdapter

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/explanation/{threadId}", response_model=ExplanationResponse)
async def get_explanation(threadId: str):
    """Get current explanation content."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    return ExplanationResponse(
        explanation=state.get("explanation", ""),
        references=state.get("explanation_references", [])
    )


@router.get("/exercise/{threadId}", response_model=ExerciseResponse)
async def get_exercise(threadId: str):
    """Get current exercise."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    exercise = state.get("exercise")
    if not exercise:
        raise HTTPException(status_code=404, detail="No exercise available")

    return ExerciseResponse(
        exerciseId=exercise.get("exercise_id", ""),
        title=exercise.get("title", ""),
        description=exercise.get("description", ""),
        starterCode=exercise.get("starter_code", ""),
        testCases=exercise.get("test_cases", []),
        hints=exercise.get("hints", []),
        difficulty=exercise.get("difficulty", "medium")
    )


@router.get("/learning-path/{threadId}", response_model=LearningPathResponse)
async def get_learning_path(threadId: str):
    """Get learning path."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    learning_path = state.get("learning_path") or state.get("current_learning_path")
    if not learning_path:
        raise HTTPException(status_code=404, detail="No learning path available")

    return LearningPathResponse(
        pathId=learning_path.get("path_id", ""),
        milestones=learning_path.get("milestones", []),
        recommendedOrder=learning_path.get("recommended_order", [])
    )