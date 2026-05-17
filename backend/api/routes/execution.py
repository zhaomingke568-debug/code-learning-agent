"""
Execution API routes - code submission and result retrieval.
"""
from fastapi import APIRouter, HTTPException
import uuid

from backend.models.schemas import CodeSubmitRequest, ExecutionResponse
from backend.agents.graph_runner import graph_runner

router = APIRouter(prefix="/api/execution", tags=["execution"])


@router.post("/submit", response_model=ExecutionResponse)
async def submit_code(req: CodeSubmitRequest):
    """Submit code for execution."""
    result = await graph_runner.submit_code(req.threadId, req.code)

    if not result:
        raise HTTPException(status_code=404, detail="Session not found")

    exec_result = result.get("executionResult", {})
    return ExecutionResponse(
        executionId=str(uuid.uuid4()),
        passed=exec_result.get("all_passed", False) or exec_result.get("passed", False),
        output=exec_result.get("output", ""),
        errorMessage=exec_result.get("error_message") or exec_result.get("main_error"),
        testResults=exec_result.get("test_results", []),
        fixSuggestions=result.get("fixSuggestions")
    )


@router.get("/{threadId}/result")
async def get_execution_result(threadId: str):
    """Get the latest execution result for a thread."""
    state = await graph_runner.get_state(threadId)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    exec_result = state.get("executionResult") or state.get("code_execution_result", {})
    return {
        "passed": exec_result.get("all_passed", False) or exec_result.get("passed", False),
        "output": exec_result.get("output", ""),
        "errorMessage": exec_result.get("error_message") or exec_result.get("main_error"),
        "testResults": exec_result.get("test_results", []),
        "summary": exec_result.get("summary", "")
    }