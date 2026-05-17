"""
FastAPI entry point for Coding Learning Agent API.
"""
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend.api.routes import session, assessment, content, execution, feedback, report
from backend.services.event_service import event_emitter
from backend.agents.graph_runner import graph_runner

app = FastAPI(
    title="Coding Learning Agent API",
    description="API for the LangGraph-based Coding Learning Agent",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session.router)
app.include_router(assessment.router)
app.include_router(content.router)
app.include_router(execution.router)
app.include_router(feedback.router)
app.include_router(report.router)


@app.get("/")
async def root():
    return {"message": "Coding Learning Agent API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/stream/{threadId}")
async def stream_events(threadId: str):
    """
    SSE endpoint for streaming events to frontend.
    """
    async def event_generator():
        async for event in event_emitter.subscribe(threadId):
            yield {
                "event": event["type"],
                "data": event["data"]
            }

    return EventSourceResponse(event_generator())


@app.post("/api/input/{threadId}")
async def provide_input(threadId: str, input_type: str, value: str):
    """
    Provide user input to a waiting session.
    Used by frontend to send assessment answers, code, or feedback.
    """
    result = await graph_runner.provide_input(threadId, input_type, value)
    if not result:
        return {"error": "Session not found"}
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)