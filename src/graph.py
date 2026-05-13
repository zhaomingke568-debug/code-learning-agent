import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

from langgraph.graph import StateGraph, START, END
from src.state import AgentState


def build_graph():
    """
    构建 Phase 1 的基础 StateGraph。

    流程：START → assess_capability → learning_path_planning
          → knowledge_explanation → exercise_generation
          → code_execution → get_feedback
          → (继续? advance_milestone → explanation : END)
    """
    workflow = StateGraph(AgentState)

    # === 导入节点 ===
    from src.nodes.assessment_node import assessment_node
    from src.nodes.learning_path_node import learning_path_node
    from src.nodes.explanation_node import explanation_node
    from src.nodes.exercise_node import exercise_node
    from src.nodes.code_execution_node import code_execution_node
    from src.nodes.feedback_node import get_feedback_node
    from src.nodes.advance_node import advance_milestone_node

    # === 注册节点 ===
    workflow.add_node("assess_capability", assessment_node)
    workflow.add_node("learning_path_planning", learning_path_node)
    workflow.add_node("knowledge_explanation", explanation_node)
    workflow.add_node("exercise_generation", exercise_node)
    workflow.add_node("code_execution", code_execution_node)
    workflow.add_node("get_feedback", get_feedback_node)
    workflow.add_node("advance_milestone", advance_milestone_node)

    # === 设置边 ===
    workflow.add_edge(START, "assess_capability")
    workflow.add_edge("assess_capability", "learning_path_planning")
    workflow.add_edge("learning_path_planning", "knowledge_explanation")
    workflow.add_edge("knowledge_explanation", "exercise_generation")
    workflow.add_edge("exercise_generation", "code_execution")
    workflow.add_edge("code_execution", "get_feedback")

    # === 反馈循环 ===
    # 用户选择继续 → advance_milestone → explanation
    # 用户选择结束 → END
    workflow.add_conditional_edges(
        "get_feedback",
        _feedback_router,
        {
            "continue": "advance_milestone",
            "end": END
        }
    )
    workflow.add_edge("advance_milestone", "knowledge_explanation")

    return workflow.compile()


def _feedback_router(state: AgentState) -> str:
    """
    反馈路由：
    - 用户满意或完成所有 milestone → END
    - 用户想继续 → advance_milestone
    """
    user_feedback = state.get("user_feedback", "").strip().lower()
    learning_path = state.get("current_learning_path", {})
    milestone_index = state.get("current_milestone_index", 0)
    milestones = learning_path.get("milestones", [])

    # 检查是否还有下一个 milestone
    has_next = (milestone_index + 1) < len(milestones)

    if not user_feedback or user_feedback in ["ok", "满意", "继续", "next", "y", "yes"]:
        if has_next:
            return "continue"
        else:
            return "end"

    if user_feedback in ["退出", "quit", "exit", "q"]:
        return "end"

    # 默认继续
    if has_next:
        return "continue"
    return "end"