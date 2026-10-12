import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


def get_supabase_client():
    """Create a Supabase client for authentication."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("Supabase authentication is not configured.")

    return create_client(url, key)


def sign_up(email, password):
    """Register a new user."""
    client = get_supabase_client()

    return client.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )


def sign_in(email, password):
    """Sign in an existing user."""
    client = get_supabase_client()

    return client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )


def sign_out(client):
    """Sign out the current user."""
    client.auth.sign_out()


def save_answer(client, user_id, question_id, sql_answer):
    """Save or update the current user's SQL answer."""
    return (
        client.table("quiz_answers")
        .upsert(
            {
                "user_id": user_id,
                "question_id": question_id,
                "sql_answer": sql_answer,
            },
            on_conflict="user_id,question_id",
        )
        .execute()
    )


def load_answers(client, user_id):
    """Load the current user's saved SQL answers."""
    response = (
        client.table("quiz_answers")
        .select("question_id, sql_answer")
        .eq("user_id", user_id)
        .execute()
    )

    return {row["question_id"]: row["sql_answer"] for row in response.data}
