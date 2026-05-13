import uuid
from src.state import AgentState


def get_feedback_node(state: AgentState) -> dict:
    """
    获取用户反馈的节点。
    询问用户是否继续下一个 milestone 或结束。
    """
    learning_path = state.get("current_learning_path", {})
    milestone_index = state.get("current_milestone_index", 0)
    milestones = learning_path.get("milestones", [])
    code_result = state.get("code_execution_result", {})

    print("\n" + "=" * 50)
    print("🤖 AI: 本次练习完成！")
    print("=" * 50)
    print(f"\n📊 执行结果：{'✅ 通过' if code_result.get('all_passed', False) else '❌ 未通过'}")
    print(f"摘要：{code_result.get('summary', 'N/A')}")

    # 检查是否还有下一个 milestone
    has_next = (milestone_index + 1) < len(milestones)

    if has_next:
        next_milestone = milestones[milestone_index + 1]
        print(f"\n📚 下一个里程碑：{next_milestone.get('topic', '未知')}")
        print(f"   {next_milestone.get('description', '')}")
        prompt = "👉 输入 '继续' 或 'next' 学习下一个里程碑，或直接回车结束："
    else:
        print("\n🎉 你已完成所有里程碑的学习！")
        prompt = "👉 输入 'ok' 或直接回车结束学习："

    feedback = input(prompt).strip().lower()

    return {"user_feedback": feedback}


def summarize_node(state: AgentState) -> dict:
    """
    记忆压缩节点。保留最后 2 条消息，将之前的消息总结。
    """
    from langchain_core.messages import RemoveMessage, HumanMessage
    import os
    from dotenv import load_dotenv
    load_dotenv(dotenv_path='.env')

    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(
        model="MiniMax-M2.5-highspeed",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        anthropic_api_url=os.getenv("ANTHROPIC_BASE_URL")
    )

    print("\n--- 🗜️ 触发记忆压缩：正在总结早期对话 ---")

    summary = state.get("summary", "")
    messages = state["messages"]

    messages_to_summarize = messages[:-2] if len(messages) > 2 else messages

    if summary:
        summary_prompt = (
            f"这是之前的对话摘要: {summary}\n\n"
            "请结合以下新产生的对话记录，更新并扩写这个摘要，保留所有关键的用户指令、偏好和已完成的规划内容：\n\n"
            f"{messages_to_summarize}"
        )
    else:
        summary_prompt = (
            f"请简要总结以下对话内容，重点记录用户的核心目标、修改要求和当前进度：\n\n"
            f"{messages_to_summarize}"
        )

    try:
        response = llm.invoke([HumanMessage(content=summary_prompt)])
        delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize]
        return {
            "summary": response.content,
            "messages": delete_messages
        }
    except Exception as e:
        print(f"总结失败: {e}")
        return {"summary": summary}