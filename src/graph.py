import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env')

from langgraph.graph import StateGraph, START, END
from src.state import AgentState


def build_graph(checkpointer=None):
    """
    构建 Phase 4 的完整 StateGraph（端到端闭环）。

    完整流程：
    START → assess_capability → learning_path_planning
          → knowledge_explanation → review(explanation)
            └─ verdict=needs_revision → 重新生成 explanation
          → exercise_generation → review(exercise)
            └─ verdict=needs_revision → 重新生成 exercise
          → code_execution → review(code)
            └─ verdict=needs_revision → 重新提交代码（user_code 清空等待输入）
          → report_generation → get_feedback
            ├─ continue → advance_milestone → explanation（下一个 milestone）
            ├─ relearn → assess_capability（重新评估）
            ├─ adjust_path → learning_path_planning（调整路径）
            └─ end → END

    Args:
        checkpointer: LangGraph checkpointer for session persistence (e.g., PostgresSaver)
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
    from src.nodes.review_node import review_node
    from src.nodes.report_node import report_node

    # === 注册节点 ===
    workflow.add_node("assess_capability", assessment_node)
    workflow.add_node("learning_path_planning", learning_path_node)
    workflow.add_node("knowledge_explanation", explanation_node)
    workflow.add_node("exercise_generation", exercise_node)
    workflow.add_node("code_execution", code_execution_node)
    workflow.add_node("get_feedback", get_feedback_node)
    workflow.add_node("advance_milestone", advance_milestone_node)
    workflow.add_node("review", review_node)
    workflow.add_node("report_generation", report_node)

    # === 设置边 ===
    workflow.add_edge(START, "assess_capability")
    workflow.add_edge("assess_capability", "learning_path_planning")
    workflow.add_edge("learning_path_planning", "knowledge_explanation")

    # === 知识讲解 → review(explanation) ===
    workflow.add_edge("knowledge_explanation", "review")

    # === exercise_generation → review(exercise) ===
    workflow.add_edge("exercise_generation", "review")

    # === code_execution → review(code) ===
    workflow.add_edge("code_execution", "review")

    # === Review verdict routing: needs_revision → back to corresponding node ===
    workflow.add_conditional_edges(
        "review",
        _review_router_str,
        {
            "continue_explanation": "knowledge_explanation",  # 讲解不通过，重新生成
            "continue_exercise": "exercise_generation",        # 练习不通过，重新生成
            "continue_code": "code_execution",               # 代码不通过，重新提交
            "continue_feedback": "get_feedback",             # 代码审核通过，进入反馈
            "continue_report": "report_generation"           # 审核通过，生成报告
        }
    )

    workflow.add_edge("report_generation", "get_feedback")

    # === Feedback router: END / 重学 / 调整路径 / 继续 ===
    workflow.add_conditional_edges(
        "get_feedback",
        _feedback_router,
        {
            "continue": "advance_milestone",
            "relearn": "assess_capability",       # 重学：从评估开始
            "adjust_path": "learning_path_planning",  # 调整路径
            "end": END
        }
    )
    workflow.add_edge("advance_milestone", "knowledge_explanation")

    return workflow.compile(checkpointer=checkpointer)


def _review_router(state: AgentState) -> dict:
    """
    Review 路由：根据 review_type 和 verdict 决定后续节点和状态更新。
    - verdict=needs_revision → 返回对应节点重新生成，同时清空相关状态
    - verdict=approved → 根据 review_type 决定后续
    返回 dict: {"next_node": str, "state_updates": dict}
    """
    review_type = state.get("review_type", "explanation")
    review_result = state.get("review_result", {})
    verdict = review_result.get("verdict", "approved")

    # 审核不通过，返回对应节点重新生成
    if verdict == "needs_revision":
        if review_type == "explanation":
            return {
                "next_node": "continue_explanation",
                "state_updates": {}  # 讲解直接重新生成即可
            }
        elif review_type == "exercise":
            return {
                "next_node": "continue_exercise",
                "state_updates": {}  # 练习题直接重新生成
            }
        elif review_type == "code":
            return {
                "next_node": "continue_code",
                "state_updates": {
                    "user_code": None,  # 清空用户代码，让用户重新输入
                    "code_execution_result": None
                }
            }

    # 审核通过，根据 review_type 决定后续
    if review_type == "explanation":
        return {"next_node": "continue_exercise", "state_updates": {}}
    elif review_type == "exercise":
        return {"next_node": "continue_code", "state_updates": {}}
    elif review_type == "code":
        return {"next_node": "continue_feedback", "state_updates": {}}
    else:
        return {"next_node": "continue_report", "state_updates": {}}


def _review_router_str(state: AgentState) -> str:
    """兼容旧接口：返回路由目标节点名称"""
    result = _review_router(state)
    return result["next_node"]


def _feedback_router(state: AgentState) -> str:
    """
    反馈路由：
    - END: 用户满意或完成所有 milestone
    - 重学 (relearn): 用户想重新学习 → assess_capability
    - 调整路径 (adjust_path): 用户想调整学习路径 → learning_path_planning
    - 继续 (continue): 进入下一个 milestone
    """
    user_feedback = state.get("user_feedback", "").strip().lower()
    learning_path = state.get("current_learning_path", {})
    milestone_index = state.get("current_milestone_index", 0)
    milestones = learning_path.get("milestones", [])

    has_next = (milestone_index + 1) < len(milestones)

    # 用户主动结束
    if user_feedback in ["退出", "quit", "exit", "q", "结束", "stop"]:
        return "end"

    # 用户想重新学习
    if user_feedback in ["重学", "relearn", "重新学习", "重新评估"]:
        return "relearn"

    # 用户想调整路径
    if user_feedback in ["调整", "调整路径", "修改路径", "change", "adjust"]:
        return "adjust_path"

    # 用户满意或继续
    if not user_feedback or user_feedback in ["ok", "满意", "继续", "next", "y", "yes", "好", "好的"]:
        if has_next:
            return "continue"
        else:
            return "end"

    # 默认：如有下一个 milestone 则继续，否则结束
    if has_next:
        return "continue"
    return "end"