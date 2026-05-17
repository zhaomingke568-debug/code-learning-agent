"""
Graph runner - async wrapper for synchronous app.invoke().
Uses ThreadPoolExecutor to run blocking invoke in separate thread.
Emits events via callback for SSE streaming.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, AsyncGenerator

from src.graph import build_graph
from src.checkpoint import create_checkpointer
from backend.services.event_service import event_emitter
from backend.agents.state_adapter import StateAdapter


class GraphRunner:
    """
    Wraps synchronous LangGraph app.invoke() for async operation.
    """

    def __init__(self):
        self._checkpointer = None
        self._app = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._sessions: Dict[str, Dict] = {}  # thread_id -> state

    def _get_app(self):
        if self._app is None:
            try:
                self._checkpointer = create_checkpointer()
            except Exception as e:
                print(f"Checkpointer creation failed, using None: {e}")
                self._checkpointer = None
            self._app = build_graph(checkpointer=self._checkpointer)
        return self._app

    def _get_config(self, thread_id: str) -> Dict:
        return {"configurable": {"thread_id": thread_id}}

    async def start_session(
        self,
        topic: str,
        depth_level: str = "进阶",
        existing_thread_id: Optional[str] = None
    ) -> tuple[str, str, str]:
        """
        Start a new learning session.
        Returns: (session_id, thread_id, status)
        """
        session_id = str(uuid.uuid4())
        thread_id = existing_thread_id or str(uuid.uuid4())

        initial_state = {
            "session_id": session_id,
            "thread_id": thread_id,
            "topic": topic,
            "depth_level": depth_level,
            "user_profile": None,
            "current_learning_path": None,
            "current_milestone_index": 0,
            "current_explanation": None,
            "explanation_references": [],
            "current_exercise": None,
            "user_code": None,
            "code_execution_result": None,
            "fix_suggestions": None,
            "review_type": None,
            "review_result": None,
            "html_report": None,
            "user_feedback": "",
            "messages": [],
            "next_step": "",
            "loop_count": 0,
            "errors": [],
            "summary": "",
            "official_docs_context": [],
            "pdf_context": [],
            "assessment_questions": [],
            "assessment_answers": [],
            "assessment_result": None,
            "waiting_for_input": None,
            "input_prompt": None,
        }

        self._sessions[thread_id] = initial_state

        return session_id, thread_id, "created"

    async def get_state(self, thread_id: str) -> Optional[Dict]:
        """Get current state for a thread."""
        app = self._get_app()
        config = self._get_config(thread_id)

        try:
            state = app.get_state(config)
            if state and state.values:
                return StateAdapter.from_agent_state(state.values)
        except Exception as e:
            # Fall back to in-memory session
            if thread_id in self._sessions:
                return StateAdapter.from_agent_state(self._sessions[thread_id])

        return None

    async def recover_session(self, thread_id: str) -> Optional[Dict]:
        """Recover session from checkpointer."""
        app = self._get_app()
        config = self._get_config(thread_id)

        try:
            state = app.get_state(config)
            if state and state.values:
                return StateAdapter.from_agent_state(state.values)
        except Exception as e:
            pass

        return None

    async def provide_input(
        self,
        thread_id: str,
        input_type: str,
        value: Any
    ) -> Optional[Dict]:
        """
        Provide user input to a waiting session.
        input_type: "assessment" | "code" | "feedback"
        """
        app = self._get_app()
        config = self._get_config(thread_id)

        try:
            # Get current state
            current_state = app.get_state(config)
            if not current_state or not current_state.values:
                return None

            # Update state with input
            updates = {"waiting_for_input": None, "input_prompt": None}

            if input_type == "assessment":
                # Store assessment answers and trigger next step
                answers = value if isinstance(value, list) else []
                updates["assessment_answers"] = answers
                updates["user_feedback"] = ""  # Clear to proceed

            elif input_type == "code":
                updates["user_code"] = value

            elif input_type == "feedback":
                updates["user_feedback"] = value

            # Update checkpoint
            app.update_state(config, updates)

            # Resume graph
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self._executor,
                lambda: app.invoke(None, config=config)
            )
            result = await future

            return StateAdapter.from_agent_state(result) if result else None

        except Exception as e:
            await event_emitter.emit_error(thread_id, str(e), "input_handler")
            return None

    async def submit_code(self, thread_id: str, code: str) -> Optional[Dict]:
        """Submit code for execution."""
        app = self._get_app()
        config = self._get_config(thread_id)

        try:
            # Get current state
            current_state = app.get_state(config)
            if not current_state or not current_state.values:
                return None

            # Update with user code
            updates = {
                "user_code": code,
                "waiting_for_input": None,
                "input_prompt": None
            }
            app.update_state(config, updates)

            # Resume graph
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                self._executor,
                lambda: app.invoke(None, config=config)
            )
            result = await future

            if result:
                state_adapter = StateAdapter()
                return {
                    "executionResult": result.get("code_execution_result"),
                    "reviewResult": result.get("review_result"),
                    "fixSuggestions": result.get("fix_suggestions"),
                }
            return None

        except Exception as e:
            await event_emitter.emit_error(thread_id, str(e), "code_submission")
            return None

    async def run_until_waiting(
        self,
        initial_state: Dict,
        thread_id: str
    ) -> AsyncGenerator[Dict, None]:
        """
        Run graph until a node needs input (waiting_for_input is set).
        Yields events for SSE.
        """
        app = self._get_app()
        config = self._get_config(thread_id)

        # Store initial state
        self._sessions[thread_id] = initial_state

        loop = asyncio.get_event_loop()

        def invoke_with_tracking():
            """Invoke with event emission."""
            result = app.invoke(initial_state, config=config)
            return result

        # Run invoke in thread pool
        future = loop.run_in_executor(self._executor, invoke_with_tracking)

        # Poll for completion or waiting state
        while not future.done():
            await asyncio.sleep(0.1)
            # Check if we should stop early (not fully implemented without checkpoint inspection)
            yield {"event": "heartbeat", "data": {"status": "running"}}

        try:
            result = await future
            yield {"event": "complete", "data": {"state": result}}
        except Exception as e:
            yield {"event": "error", "data": {"message": str(e)}}


# Global graph runner instance
graph_runner = GraphRunner()