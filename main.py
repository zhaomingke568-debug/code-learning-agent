import os
import uuid
from dotenv import load_dotenv

from src.graph import build_graph

# Load environment variables
load_dotenv(dotenv_path='.env')


def main():
    # Verify API Keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment variables.")
        return

    print("=" * 60)
    print("🎓 Welcome to Coding Learning Agent!")
    print("=" * 60)

    # User Input
    topic = input("\n📝 请输入你想学习的主题（如：Python 装饰器、FastAPI 路由设计）: ").strip()
    if not topic:
        print("学习主题不能为空！")
        return

    depth = input("🎯 目标级别（直接回车默认「进阶」: 入门 / 进阶 / 专家）: ").strip() or "进阶"
    if depth not in ["入门", "进阶", "专家"]:
        print("无效的级别，使用默认「进阶」")
        depth = "进阶"

    session_id = str(uuid.uuid4())
    thread_id = input("🔄 会话 ID（直接回车使用新会话，或输入已有 ID 恢复）: ").strip() or session_id

    print(f"\n--- 🚀 开始学习：{topic} (目标: {depth}) ---\n")

    # Initialize State - 匹配新的 AgentState schema
    initial_state = {
        # 会话身份
        "session_id": session_id,
        "thread_id": thread_id,

        # 用户输入
        "topic": topic,
        "depth_level": depth,

        # 用户画像（初始为空，后续由 assessment_node 填充）
        "user_profile": None,

        # 学习路径
        "current_learning_path": None,
        "current_milestone_index": 0,

        # 知识点讲解
        "current_explanation": None,
        "explanation_references": [],

        # 练习相关
        "current_exercise": None,
        "user_code": None,
        "code_execution_result": None,
        "fix_suggestions": None,

        # Review
        "review_type": None,
        "review_result": None,

        # 输出
        "html_report": None,
        "user_feedback": "",

        # 状态管理
        "messages": [],
        "next_step": "",
        "loop_count": 0,
        "errors": [],
        "summary": "",

        # RAG 上下文
        "official_docs_context": [],
        "pdf_context": [],

        # 诊断相关
        "assessment_questions": [],
        "assessment_answers": [],
        "assessment_result": None,
    }

    # Build and Run Graph
    app = build_graph()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = app.invoke(initial_state, config=config)

        print("\n" + "=" * 60)
        print("🎉 学习流程完成！")
        print("=" * 60)

        # 输出执行结果摘要
        code_result = final_state.get("code_execution_result", {})
        print(f"\n📊 最终执行结果：{'✅ 通过' if code_result.get('all_passed', False) else '❌ 未通过'}")
        print(f"   摘要：{code_result.get('summary', 'N/A')}")

        # 保存 HTML 报告（如果有）
        html_report = final_state.get("html_report") or final_state.get("final_report")
        if html_report:
            filename = f"learning_report_{topic.replace(' ', '_')}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_report)
            print(f"\n📄 报告已保存到：{filename}")

    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()