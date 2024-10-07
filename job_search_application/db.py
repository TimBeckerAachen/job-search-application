import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


RUN_TIMEZONE_CHECK = os.getenv('RUN_TIMEZONE_CHECK', '1') == '1'
TZ_INFO = os.getenv("TZ", "Europe/Berlin")
tz = ZoneInfo(TZ_INFO)


def create_db_if_not_exists():
    print(os.getenv("POSTGRES_HOST", "localhost"))
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        database="postgres",
        user=os.getenv("POSTGRES_USER", "username"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with conn.cursor() as cur:
            # Check if the database exists
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                        (os.getenv("POSTGRES_DB", "job_search_application"),))
            exists = cur.fetchone()

            if not exists:
                # Create the database
                cur.execute(f"CREATE DATABASE {os.getenv('POSTGRES_DB', 'job_search_application')}")
                print(f"Database '{os.getenv('POSTGRES_DB', 'job_search_application')}' created successfully.")
            else:
                print(f"Database '{os.getenv('POSTGRES_DB', 'job_search_application')}' already exists.")
    finally:
        conn.close()


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        database=os.getenv("POSTGRES_DB", "job_search_application"),
        user=os.getenv("POSTGRES_USER", "username"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )


def init_db():
    create_db_if_not_exists()
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")
            cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE conversations (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model_used TEXT NOT NULL,
                    response_time FLOAT NOT NULL,
                    relevance TEXT NOT NULL,
                    relevance_explanation TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    eval_prompt_tokens INTEGER NOT NULL,
                    eval_completion_tokens INTEGER NOT NULL,
                    eval_total_tokens INTEGER NOT NULL,
                    a21_cost FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id TEXT REFERENCES conversations(id),
                    feedback INTEGER NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()


def save_conversation(conversation_id, query, response_data, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations
                (id, query, response, model_used, response_time, relevance,
                relevance_explanation, prompt_tokens, completion_tokens, total_tokens,
                eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, a21_cost, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,

                (
                    conversation_id,
                    query,
                    response_data["response"],
                    response_data["model_used"],
                    response_data["response_time"],
                    response_data["relevance"],
                    response_data["relevance_explanation"],
                    response_data["prompt_tokens"],
                    response_data["completion_tokens"],
                    response_data["total_tokens"],
                    response_data["eval_prompt_tokens"],
                    response_data["eval_completion_tokens"],
                    response_data["eval_total_tokens"],
                    response_data["a21_cost"],
                    timestamp
                ),
            )
        conn.commit()
    finally:
        conn.close()


def save_feedback(conversation_id, feedback, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO feedback (conversation_id, feedback, timestamp) VALUES (%s, %s, COALESCE(%s, CURRENT_TIMESTAMP))",
                (conversation_id, feedback, timestamp),
            )
        conn.commit()
    finally:
        conn.close()


def get_recent_conversations(limit=5, relevance=None):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            query = """
                SELECT c.*, f.feedback
                FROM conversations c
                LEFT JOIN feedback f ON c.id = f.conversation_id
            """
            if relevance:
                query += f" WHERE c.relevance = '{relevance}'"
            query += " ORDER BY c.timestamp DESC LIMIT %s"

            cur.execute(query, (limit,))
            return cur.fetchall()
    finally:
        conn.close()


def get_feedback_stats():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN feedback > 0 THEN 1 ELSE 0 END) as thumbs_up,
                    SUM(CASE WHEN feedback < 0 THEN 1 ELSE 0 END) as thumbs_down
                FROM feedback
            """)
            return cur.fetchone()
    finally:
        conn.close()


def check_timezone():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW timezone;")
            db_timezone = cur.fetchone()[0]
            print(f"Database timezone: {db_timezone}")

            cur.execute("SELECT current_timestamp;")
            db_time_utc = cur.fetchone()[0]
            print(f"Database current time (UTC): {db_time_utc}")

            db_time_local = db_time_utc.astimezone(tz)
            print(f"Database current time ({TZ_INFO}): {db_time_local}")

            py_time = datetime.now(tz)
            print(f"Python current time: {py_time}")

            # Use py_time instead of tz for insertion
            cur.execute("""
               INSERT INTO conversations
               (id, query, response, model_used, response_time, relevance,
               relevance_explanation, prompt_tokens, completion_tokens, total_tokens,
               eval_prompt_tokens, eval_completion_tokens, eval_total_tokens, a21_cost, timestamp)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING timestamp;
            """,
            ('test', 'test query', 'test response', 'test model', 0.0, 0.0,
            'test explanation', 0, 0, 0, 0, 0, 0, 0.0, py_time))
            inserted_time = cur.fetchone()[0]
            print(f"Inserted time (UTC): {inserted_time}")
            print(f"Inserted time ({TZ_INFO}): {inserted_time.astimezone(tz)}")

            cur.execute("SELECT timestamp FROM conversations WHERE id = 'test';")
            selected_time = cur.fetchone()[0]
            print(f"Selected time (UTC): {selected_time}")
            print(f"Selected time ({TZ_INFO}): {selected_time.astimezone(tz)}")

            # Clean up the test entry
            cur.execute("DELETE FROM conversations WHERE id = 'test';")
            conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()


if RUN_TIMEZONE_CHECK:
    check_timezone()
