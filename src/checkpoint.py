"""
Checkpoint module using LangGraph's checkpointer for session persistence.
Supports PostgreSQL (PostgresSaver) for production, MemorySaver for testing.
"""
import os
from typing import Optional

from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


def create_checkpointer():
    """
    Create a checkpointer for session persistence.
    Uses PostgresSaver if PostgreSQL is configured, otherwise MemorySaver.
    """
    # Try PostgreSQL first
    if os.getenv("POSTGRES_HOST"):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            connection_kwargs = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": os.getenv("POSTGRES_PORT", "5432"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
                "database": os.getenv("POSTGRES_DB", "learning_agent"),
            }
            # Try async version first (newer)
            try:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                return AsyncPostgresSaver.from_conn_func(
                    lambda: __import__('psycopg').connect(**connection_kwargs)
                )
            except Exception:
                pass
            # Fall back to sync
            return PostgresSaver.from_conn_func(
                lambda: __import__('psycopg2').connect(**connection_kwargs)
            )
        except Exception as e:
            print(f"⚠️ PostgreSQL checkpointer unavailable: {e}")

    # Fall back to MemorySaver for testing/dev
    from langgraph.checkpoint.memory import MemorySaver
    print("💾 Using MemorySaver (in-memory, non-persistent)")
    return MemorySaver()


def create_postgres_saver():
    """
    Create a synchronous PostgresSaver for checkpointing (if PostgreSQL available).
    """
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        connection_kwargs = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "database": os.getenv("POSTGRES_DB", "learning_agent"),
        }
        return PostgresSaver.from_conn_func(
            lambda: __import__('psycopg2').connect(**connection_kwargs)
        )
    except Exception as e:
        raise RuntimeError(f"PostgreSQL checkpointer unavailable: {e}")


def init_postgres_schema():
    """
    Initialize the PostgreSQL schema for LangGraph checkpointing.
    Requires psycopg2 and PostgreSQL connection.
    """
    try:
        import psycopg2
    except ImportError:
        print("⚠️ psycopg2 not installed, skipping schema init")
        return

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "learning_agent")

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT NOT NULL,
                    data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (thread_id, checkpoint_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkpoint_writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    value JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (thread_id, checkpoint_id, task_id, idx)
                )
            """)
            conn.commit()
        conn.close()
        print("✅ PostgreSQL checkpoint schema initialized")
    except Exception as e:
        print(f"⚠️ Cannot initialize PostgreSQL schema: {e}")


if __name__ == "__main__":
    checkpointer = create_checkpointer()
    print(f"✅ Checkpointer ready: {type(checkpointer).__name__}")