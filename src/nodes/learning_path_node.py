import os
import uuid
from typing import List, Dict

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

from src.state import AgentState
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


llm = ChatAnthropic(
    model="MiniMax-M2.7",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    anthropic_api_url=os.getenv("ANTHROPIC_BASE_URL"),
    max_retries=5
)


def learning_path_node(state: AgentState) -> dict:
    """
    根据评估结果生成个性化学习路径。
    """
    topic = state["topic"]
    depth_level = state.get("depth_level", "入门")
    assessment_result = state.get("assessment_result", {})
    user_profile = state.get("user_profile", {})

    print(f"\n--- 🗺️ 生成学习路径：{topic} ---")

    # 获取用户的 level 和 weak_points
    user_level = assessment_result.get("level", depth_level)
    weak_points = assessment_result.get("weaknesses", [])
    strong_points = assessment_result.get("strengths", [])

    # 生成学习路径
    learning_path = _generate_learning_path(topic, user_level, weak_points, strong_points)

    print(f"\n--- 📚 学习路径已生成 ---")
    print(f"路径包含 {len(learning_path['milestones'])} 个里程碑：")
    for i, m in enumerate(learning_path["milestones"], 1):
        print(f"  {i}. {m['topic']} ({m.get('duration_hours', 1)}小时)")

    return {
        "current_learning_path": learning_path,
        "current_milestone_index": 0,
        "next_step": "knowledge_explanation"
    }


def _generate_learning_path(topic: str, user_level: str, weak_points: List[str], strong_points: List[str]) -> Dict:
    """使用 LLM 生成学习路径"""
    system_prompt = """你是一个专业的编程学习规划师。根据用户的学习主题、目标级别和薄弱点，生成一个结构化的学习路径。

主题：{topic}
用户评估水平：{user_level}
用户薄弱点：{weak_points}
用户强项：{strong_points}

要求：
1. 路径应该从基础到进阶，循序渐进
2. 针对薄弱点安排更多练习
3. 每个里程碑包含：topic（主题）、description（简短描述）、duration_hours（预估小时数）
4. 推荐顺序（recommended_order）是 milestone 的 topic 列表
5. 一般 3-5 个里程碑

输出格式（严格 JSON）：
{{"path_id": "uuid",
  "milestones": [
    {{"topic": "基础知识", "description": "掌握核心概念", "duration_hours": 2}},
    {{"topic": "进阶用法", "description": "深入理解", "duration_hours": 3}},
    {{"topic": "实战练习", "description": "项目实战", "duration_hours": 4}}
  ],
  "recommended_order": ["基础知识", "进阶用法", "实战练习"]
}}
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "为「{topic}」生成学习路径")
    ])

    parser = JsonOutputParser(pydantic_object=dict)

    try:
        chain = prompt | llm | parser
        result = chain.invoke({
            "topic": topic,
            "user_level": user_level,
            "weak_points": weak_points,
            "strong_points": strong_points
        })
        # 确保有 path_id
        if "path_id" not in result:
            result["path_id"] = str(uuid.uuid4())
        return result
    except Exception as e:
        print(f"生成学习路径失败，使用默认路径: {e}")
        # 返回默认路径
        return {
            "path_id": str(uuid.uuid4()),
            "milestones": [
                {"topic": "基础概念", "description": f"学习{topic}的基础知识", "duration_hours": 2},
                {"topic": "核心用法", "description": f"掌握{topic}的核心用法", "duration_hours": 3},
                {"topic": "实战应用", "description": f"{topic}的实战项目", "duration_hours": 4}
            ],
            "recommended_order": ["基础概念", "核心用法", "实战应用"]
        }