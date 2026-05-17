"""
Profile store using PostgreSQL for user profile persistence.
Auto-updates weak_points/strong_points after code execution.
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')

import psycopg2
from psycopg2.extras import RealDictCursor


POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "learning_agent")


def get_connection():
    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DB,
    )


class ProfileStore:
    """
    PostgreSQL-backed user profile store.
    Tracks learning history, weak/strong points, and preferences.
    """

    def __init__(self):
        self._ensure_table()

    def _ensure_table(self):
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id TEXT PRIMARY KEY,
                        capability_level TEXT NOT NULL DEFAULT '入门',
                        weak_points JSONB NOT NULL DEFAULT '[]',
                        strong_points JSONB NOT NULL DEFAULT '[]',
                        learning_history JSONB NOT NULL DEFAULT '[]',
                        preferences JSONB NOT NULL DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id."""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM user_profiles WHERE user_id = %s",
                    (user_id,)
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
                return None

    def save_profile(self, profile: Dict[str, Any]) -> bool:
        """Save or update user profile."""
        user_id = profile.get("user_id")
        if not user_id:
            return False

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO user_profiles (user_id, capability_level, weak_points, strong_points, learning_history, preferences, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE SET
                        capability_level = EXCLUDED.capability_level,
                        weak_points = EXCLUDED.weak_points,
                        strong_points = EXCLUDED.strong_points,
                        learning_history = EXCLUDED.learning_history,
                        preferences = EXCLUDED.preferences,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    user_id,
                    profile.get("capability_level", "入门"),
                    json.dumps(profile.get("weak_points", [])),
                    json.dumps(profile.get("strong_points", [])),
                    json.dumps(profile.get("learning_history", [])),
                    json.dumps(profile.get("preferences", {}))
                ))
                conn.commit()
                return True

    def update_from_code_result(self, user_id: str, topic: str, passed: bool, score: float = 0.0):
        """
        Auto-update weak_points/strong_points based on code execution result.
        Called after code review or execution.
        """
        profile = self.get_profile(user_id)
        if not profile:
            profile = {
                "user_id": user_id,
                "capability_level": "入门",
                "weak_points": [],
                "strong_points": [],
                "learning_history": [],
                "preferences": {}
            }

        weak_points = json.loads(profile.get("weak_points", "[]")) if isinstance(profile.get("weak_points"), str) else profile.get("weak_points", [])
        strong_points = json.loads(profile.get("strong_points", "[]")) if isinstance(profile.get("strong_points"), str) else profile.get("strong_points", [])
        learning_history = json.loads(profile.get("learning_history", "[]")) if isinstance(profile.get("learning_history"), str) else profile.get("learning_history", [])

        # Record this learning session
        learning_history.append({
            "topic": topic,
            "completed_at": datetime.now().isoformat(),
            "score": score,
            "passed": passed
        })

        # Update weak/strong points based on performance
        if passed:
            if topic not in strong_points:
                strong_points.append(topic)
            weak_points = [wp for wp in weak_points if wp != topic]
        else:
            if topic not in weak_points:
                weak_points.append(topic)
            strong_points = [sp for sp in strong_points if sp != topic]

        profile["weak_points"] = weak_points
        profile["strong_points"] = strong_points
        profile["learning_history"] = learning_history

        self.save_profile(profile)
        print(f"📊 Profile updated for {user_id}: strong={strong_points}, weak={weak_points}")

    def update_capability_level(self, user_id: str, level: str):
        """Update user's capability level after assessment."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE user_profiles
                    SET capability_level = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, (level, user_id))
                conn.commit()

    def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
                conn.commit()
                return cur.rowcount > 0


if __name__ == "__main__":
    store = ProfileStore()

    # Test CRUD
    test_profile = {
        "user_id": f"test_user_{uuid.uuid4().hex[:8]}",
        "capability_level": "进阶",
        "weak_points": ["闭包", "装饰器"],
        "strong_points": ["基础语法"],
        "learning_history": [],
        "preferences": {"style": "practice"}
    }
    store.save_profile(test_profile)

    retrieved = store.get_profile(test_profile["user_id"])
    print(f"✅ Profile store test: {retrieved['user_id']} - {retrieved['capability_level']}")