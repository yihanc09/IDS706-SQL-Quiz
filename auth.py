"""Supabase authentication and per-user quiz answer persistence."""
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured.")
    return create_client(url, key)


def sign_up(email, password):
    return get_supabase_client().auth.sign_up({"email": email, "password": password})


def sign_in(email, password):
    return get_supabase_client().auth.sign_in_with_password({"email": email, "password": password})


def sign_out(client):
    client.auth.sign_out()


def save_answer(client, user_id, question_id, sql_answer):
    """Save a draft; clear any previous grade for that answer."""
    return client.table("quiz_answers").upsert(
        {
            "user_id": user_id,
            "question_id": question_id,
            "sql_answer": sql_answer,
            "score": None,
            "is_correct": None,
        },
        on_conflict="user_id,question_id",
    ).execute()


def save_graded_answer(client, user_id, question_id, sql_answer, score, is_correct):
    """Persist SQL and its grade in the same upsert operation."""
    return client.table("quiz_answers").upsert(
        {
            "user_id": user_id,
            "question_id": question_id,
            "sql_answer": sql_answer,
            "score": score,
            "is_correct": is_correct,
        },
        on_conflict="user_id,question_id",
    ).execute()


def load_answer_records(client, user_id):
    """Return per-question SQL and saved grade for the authenticated user."""
    response = (
        client.table("quiz_answers")
        .select("question_id,sql_answer,score,is_correct")
        .eq("user_id", user_id)
        .execute()
    )
    return {row["question_id"]: row for row in response.data}


def load_answers(client, user_id):
    """Backward-compatible helper returning only SQL text."""
    return {
        question_id: row["sql_answer"]
        for question_id, row in load_answer_records(client, user_id).items()
    }
