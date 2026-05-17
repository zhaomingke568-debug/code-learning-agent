"""
Event service - SSE event emission and subscription management.
"""
import asyncio
import json
from typing import Dict, AsyncGenerator, Optional
from datetime import datetime


class EventEmitter:
    """
    Central event emission for SSE streaming.
    Frontend subscribes to thread-specific event streams.
    """

    def __init__(self):
        self._subscribers: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, thread_id: str) -> AsyncGenerator[Dict, None]:
        """Subscribe to events for a thread."""
        async with self._lock:
            if thread_id not in self._subscribers:
                self._subscribers[thread_id] = asyncio.Queue()
            queue = self._subscribers[thread_id]

        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                if thread_id in self._subscribers and self._subscribers[thread_id] is queue:
                    del self._subscribers[thread_id]

    async def emit(self, thread_id: str, event_type: str, data: Dict):
        """Emit event to subscriber."""
        async with self._lock:
            if thread_id not in self._subscribers:
                return
            queue = self._subscribers[thread_id]

        event = {"type": event_type, "data": data}
        await queue.put(event)

    async def emit_node_start(self, thread_id: str, node_name: str):
        await self.emit(thread_id, "node_start", {
            "nodeName": node_name,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def emit_node_complete(self, thread_id: str, node_name: str, output: Dict):
        await self.emit(thread_id, "node_complete", {
            "nodeName": node_name,
            "output": output,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def emit_streaming(self, thread_id: str, content: str, node_name: str):
        await self.emit(thread_id, "streaming_output", {
            "content": content,
            "nodeName": node_name
        })

    async def emit_waiting_input(
        self,
        thread_id: str,
        input_type: str,
        prompt: str,
        exercise_id: Optional[str] = None
    ):
        data = {
            "inputType": input_type,
            "prompt": prompt,
            "timestamp": datetime.utcnow().isoformat()
        }
        if exercise_id:
            data["exerciseId"] = exercise_id
        await self.emit(thread_id, "waiting_input", data)

    async def emit_error(self, thread_id: str, message: str, node_name: str):
        await self.emit(thread_id, "error", {
            "message": message,
            "nodeName": node_name,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def emit_complete(self, thread_id: str, final_state: Dict):
        await self.emit(thread_id, "complete", {
            "finalState": final_state,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def emit_assessment_questions(self, thread_id: str, questions: list):
        await self.emit(thread_id, "assessment_questions", {
            "questions": questions,
            "timestamp": datetime.utcnow().isoformat()
        })


# Global event emitter instance
event_emitter = EventEmitter()