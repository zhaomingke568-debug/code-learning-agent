"""
Report node: Generate learning progress report in console format.
No HTML - just text output showing milestones, accuracy, weak points.
"""
from src.state import AgentState


def report_node(state: AgentState) -> dict:
    """
    Generate learning progress report in console format.
    Shows: completed milestones, correct rate, weak points.
    """
    topic = state.get("topic", "未知")
    learning_path = state.get("current_learning_path", {})
    milestone_index = state.get("current_milestone_index", 0)
    assessment_result = state.get("assessment_result", {})
    code_execution_result = state.get("code_execution_result", {})
    user_profile = state.get("user_profile", {})
    current_exercise = state.get("current_exercise", {})

    milestones = learning_path.get("milestones", [])
    completed_count = milestone_index + 1
    total_milestones = len(milestones)

    # Calculate accuracy from assessment
    assessment_answers = state.get("assessment_answers", [])
    assessment_questions = state.get("assessment_questions", [])
    correct_rate = 0.0
    if assessment_questions and assessment_answers:
        correct = sum(1 for ans in assessment_answers if ans.get("correct", False))
        correct_rate = correct / len(assessment_answers) if assessment_answers else 0.0

    # Weak/strong points from profile
    weak_points = user_profile.get("weak_points", []) if isinstance(user_profile, dict) else []
    strong_points = user_profile.get("strong_points", []) if isinstance(user_profile, dict) else []

    # Code execution result
    code_passed = code_execution_result.get("passed", False) if code_execution_result else False
    code_summary = code_execution_result.get("summary", "N/A") if code_execution_result else "N/A"

    print("\n" + "=" * 60)
    print("📊 学习进度报告")
    print("=" * 60)

    print(f"\n📚 学习主题: {topic}")
    print(f"🎯 目标级别: {state.get('depth_level', '未知')}")

    # Assessment results
    print(f"\n--- 能力评估 ---")
    print(f"评估级别: {assessment_result.get('level', '未评估')}")
    print(f"正确率: {correct_rate * 100:.0f}%")

    if assessment_result.get("strengths"):
        print(f"✅ 强项: {', '.join(assessment_result['strengths'])}")
    if assessment_result.get("weaknesses"):
        print(f"⚠️ 薄弱点: {', '.join(assessment_result['weaknesses'])}")

    # Learning path progress
    print(f"\n--- 学习路径进度 ---")
    print(f"里程碑: {completed_count}/{total_milestones} 完成")
    if milestones:
        print("已完成里程碑:")
        for i, m in enumerate(milestones[:completed_count]):
            print(f"  ✅ {i+1}. {m.get('topic', '未知')}")
        if completed_count < total_milestones:
            print("当前里程碑:")
            print(f"  🔄 {completed_count+1}. {milestones[completed_count].get('topic', '未知')}")

    # Code execution
    print(f"\n--- 代码执行结果 ---")
    print(f"状态: {'✅ 通过' if code_passed else '❌ 未通过'}")
    print(f"摘要: {code_summary}")

    # Current exercise
    if current_exercise:
        print(f"练习题: {current_exercise.get('title', '未知')}")
        print(f"难度: {current_exercise.get('difficulty', '未知')}")

    # User profile weak/strong points
    print(f"\n--- 用户画像 ---")
    print(f"强项: {', '.join(strong_points) if strong_points else '暂无'}")
    print(f"薄弱点: {', '.join(weak_points) if weak_points else '暂无'}")

    # Learning history
    history = user_profile.get("learning_history", []) if isinstance(user_profile, dict) else []
    if history:
        print(f"历史学习记录: {len(history)} 次")

    print("\n" + "=" * 60)

    return {
        "next_step": "get_feedback"
    }