"""
State adapter - converts between API response format and AgentState format.
"""
from typing import Dict, Any, Optional


class StateAdapter:
    """
    Converts between FastAPI response models and LangGraph AgentState.
    """

    @staticmethod
    def to_agent_state(api_state: Dict) -> Dict:
        """Convert API state dict to AgentState format."""
        return {
            "session_id": api_state.get("sessionId", api_state.get("session_id")),
            "thread_id": api_state.get("threadId", api_state.get("thread_id")),
            "topic": api_state.get("topic"),
            "depth_level": api_state.get("depthLevel", api_state.get("depth_level", "进阶")),
            "user_profile": api_state.get("userProfile", api_state.get("user_profile")),
            "current_learning_path": api_state.get("learningPath", api_state.get("current_learning_path")),
            "current_milestone_index": api_state.get("milestoneIndex", api_state.get("current_milestone_index", 0)),
            "current_explanation": api_state.get("explanation", api_state.get("current_explanation")),
            "current_exercise": api_state.get("exercise", api_state.get("current_exercise")),
            "user_code": api_state.get("userCode", api_state.get("user_code")),
            "code_execution_result": api_state.get("executionResult", api_state.get("code_execution_result")),
            "review_type": api_state.get("reviewType", api_state.get("review_type")),
            "review_result": api_state.get("reviewResult", api_state.get("review_result")),
            "user_feedback": api_state.get("userFeedback", api_state.get("user_feedback", "")),
            "messages": api_state.get("messages", []),
            "next_step": api_state.get("nextStep", api_state.get("next_step", "")),
            "loop_count": api_state.get("loopCount", api_state.get("loop_count", 0)),
            "errors": api_state.get("errors", []),
            "summary": api_state.get("summary", ""),
            "official_docs_context": api_state.get("officialDocsContext", api_state.get("official_docs_context", [])),
            "pdf_context": api_state.get("pdfContext", api_state.get("pdf_context", [])),
            "assessment_questions": api_state.get("assessmentQuestions", api_state.get("assessment_questions", [])),
            "assessment_answers": api_state.get("assessmentAnswers", api_state.get("assessment_answers", [])),
            "assessment_result": api_state.get("assessmentResult", api_state.get("assessment_result")),
            "waiting_for_input": api_state.get("waitingForInput", api_state.get("waiting_for_input")),
            "input_prompt": api_state.get("inputPrompt", api_state.get("input_prompt")),
        }

    @staticmethod
    def from_agent_state(agent_state: Dict) -> Dict:
        """Convert AgentState to API response format."""
        return {
            "sessionId": agent_state.get("session_id"),
            "threadId": agent_state.get("thread_id"),
            "topic": agent_state.get("topic"),
            "depthLevel": agent_state.get("depth_level"),
            "userProfile": agent_state.get("user_profile"),
            "learningPath": agent_state.get("current_learning_path"),
            "milestoneIndex": agent_state.get("current_milestone_index", 0),
            "explanation": agent_state.get("current_explanation"),
            "exercise": agent_state.get("current_exercise"),
            "userCode": agent_state.get("user_code"),
            "executionResult": agent_state.get("code_execution_result"),
            "reviewType": agent_state.get("review_type"),
            "reviewResult": agent_state.get("review_result"),
            "assessmentResult": agent_state.get("assessment_result"),
            "waitingForInput": agent_state.get("waiting_for_input"),
            "inputPrompt": agent_state.get("input_prompt"),
            "isComplete": agent_state.get("next_step") == "END" if agent_state.get("next_step") else False,
        }

    @staticmethod
    def extract_explanation(agent_state: Dict) -> Dict:
        """Extract explanation data from agent state."""
        return {
            "explanation": agent_state.get("current_explanation", ""),
            "references": agent_state.get("explanation_references", []),
        }

    @staticmethod
    def extract_exercise(agent_state: Dict) -> Optional[Dict]:
        """Extract exercise data from agent state."""
        exercise = agent_state.get("current_exercise")
        if not exercise:
            return None
        return {
            "exerciseId": exercise.get("exercise_id", ""),
            "title": exercise.get("title", ""),
            "description": exercise.get("description", ""),
            "starterCode": exercise.get("starter_code", ""),
            "testCases": exercise.get("test_cases", []),
            "hints": exercise.get("hints", []),
            "difficulty": exercise.get("difficulty", "medium"),
        }

    @staticmethod
    def extract_learning_path(agent_state: Dict) -> Optional[Dict]:
        """Extract learning path from agent state."""
        return agent_state.get("current_learning_path")

    @staticmethod
    def extract_assessment_result(agent_state: Dict) -> Optional[Dict]:
        """Extract assessment result from agent state."""
        return agent_state.get("assessment_result")

    @staticmethod
    def extract_report(agent_state: Dict) -> Dict:
        """Extract report data from agent state."""
        user_profile = agent_state.get("user_profile", {}) or {}
        return {
            "topic": agent_state.get("topic", ""),
            "depthLevel": agent_state.get("depth_level", ""),
            "assessmentResult": agent_state.get("assessment_result", {}),
            "completedMilestones": agent_state.get("current_learning_path", {}).get("milestones", [])[:agent_state.get("current_milestone_index", 0) + 1],
            "codeExecutionResult": agent_state.get("code_execution_result", {}),
            "weakPoints": user_profile.get("weak_points", []),
            "strongPoints": user_profile.get("strong_points", []),
            "learningHistory": user_profile.get("learning_history", []),
        }