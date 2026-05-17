from typing import List, TypedDict, Optional, Annotated, Dict, Any
import operator

from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


# === TypedDict Classes ===

class UserProfile(TypedDict):
    """用户画像"""
    user_id: str
    capability_level: str  # "入门" / "进阶" / "专家"
    weak_points: List[str]  # 薄弱知识点
    strong_points: List[str]  # 强项知识点
    learning_history: List[dict]  # [{"topic": str, "completed_at": str, "score": float, "passed": bool}]
    preferences: dict  # 学习偏好


class Exercise(TypedDict):
    """练习题"""
    exercise_id: str
    title: str
    description: str
    starter_code: str  # 用户看到的起始代码
    solution_code: str  # 正确答案（用于 review 验证）
    test_cases: List[dict]  # [{"input": str, "expected": str, "hidden": bool}]
    hints: List[str]
    difficulty: str  # "easy" / "medium" / "hard"
    topic_tags: List[str]  # 关联的知识点


class CodeExecutionResult(TypedDict):
    """代码执行结果"""
    execution_id: str
    passed: bool
    output: str
    error_message: Optional[str]
    error_line: Optional[int]
    test_results: List[dict]  # [{"test_id": str, "passed": bool, "message": str}]


class LearningPath(TypedDict):
    """学习路径"""
    path_id: str
    milestones: List[dict]  # [{"topic": str, "description": str, "duration_hours": float}]
    recommended_order: List[str]  # milestone 顺序


class MilestoneReference(TypedDict):
    """讲解中引用的文档来源"""
    source: str
    content: str
    page: Optional[int]


# === Main State ===

class AgentState(TypedDict):
    # === 会话身份 ===
    session_id: str
    thread_id: str  # LangGraph checkpoint

    # === 用户输入 ===
    topic: str  # 学习目标，如 "Python 装饰器"
    depth_level: str  # "入门" / "进阶" / "专家"

    # === 用户画像（持久化）===
    user_profile: Optional[UserProfile]

    # === 学习路径 ===
    current_learning_path: Optional[LearningPath]
    current_milestone_index: int = 0  # 当前在路径中的位置

    # === 知识点讲解 ===
    current_explanation: Optional[str]  # 当前生成的讲解内容
    explanation_references: List[MilestoneReference]  # 引用的 RAG 文档

    # === 练习相关 ===
    current_exercise: Optional[Exercise]  # 当前练习题
    user_code: Optional[str]  # 用户提交的代码
    code_execution_result: Optional[CodeExecutionResult]  # 执行结果
    fix_suggestions: Optional[str]  # 代码修复建议

    # === Review ===
    review_type: Optional[str]  # "explanation" / "code" / "exercise"
    review_result: Optional[dict]  # {"verdict": "approved"|"needs_revision", "correctness_score": float, "issues": List[str], "suggestions": List[str]}

    # === 输出 ===
    html_report: Optional[str]
    user_feedback: str

    # === 状态管理 ===
    messages: Annotated[List[AnyMessage], add_messages]
    next_step: str
    loop_count: int = 0
    errors: Annotated[List[str], operator.add]
    summary: str  # 对话摘要

    # === RAG 上下文 ===
    official_docs_context: Annotated[List[dict], operator.add]  # 官方文档 RAG
    pdf_context: Annotated[List[dict], operator.add]  # 本地 PDF 的 RAG

    # === 诊断相关 ===
    assessment_questions: List[dict]  # [{"question": str, "options": [...], "correct_answer": str}]
    assessment_answers: List[dict]  # 用户回答 [{"question_id": str, "answer": str}]
    assessment_result: Optional[dict]  # {"level": str, "strengths": [...], "weaknesses": [...]}

    # === Web API 模式 ===
    waiting_for_input: Optional[str] = None  # "assessment" | "code" | "feedback" | None
    input_prompt: Optional[str] = None  # 显示给用户的提示文本