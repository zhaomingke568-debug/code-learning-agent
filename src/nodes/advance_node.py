from src.state import AgentState


def advance_milestone_node(state: AgentState) -> dict:
    """
    推进到下一个里程碑的节点。
    在继续学习时被调用，更新 milestone_index。
    """
    learning_path = state.get("current_learning_path", {})
    milestones = learning_path.get("milestones", [])
    current_index = state.get("current_milestone_index", 0)

    new_index = current_index + 1
    next_topic = milestones[new_index].get("topic", "未知") if new_index < len(milestones) else ""

    print(f"\n--- ⏭️ 推进到下一个里程碑: {next_topic} ---")

    return {
        "current_milestone_index": new_index,
        # 重置相关状态
        "current_exercise": None,
        "user_code": None,
        "code_execution_result": None,
        "fix_suggestions": None,
    }


def end_learning_node(state: AgentState) -> dict:
    """
    结束学习的节点。
    """
    print("\n--- 👋 学习结束，感谢使用！---")
    return {"user_feedback": ""}


# 重新导出 get_feedback_node 以便 graph.py 导入
from src.nodes.feedback_node import get_feedback_node