import streamlit as st

from auth import (
    get_supabase_client,
    sign_in,
    sign_up,
    save_answer,
    load_answers,
)

from database import run_query
from quiz import get_questions, get_total_points

st.set_page_config(
    page_title="IDS706 SQL Quiz",
    page_icon="🎓",
    layout="wide",
)

st.title("IDS706 SQL Quiz")
st.caption("Practice SQL with the Chinook Music Store Database")

# Store authentication state for the current browser session.
if "user" not in st.session_state:
    st.session_state.user = None

if "supabase_client" not in st.session_state:
    st.session_state.supabase_client = None


if st.session_state.user is None:
    st.subheader("Welcome!")

    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            login_button = st.form_submit_button("Sign In")

        if login_button:
            try:
                response = sign_in(email, password)

                if response.user and response.session:
                    st.session_state.user = response.user
                    st.session_state.supabase_client = get_supabase_client()
                    st.session_state.supabase_client.auth.set_session(
                        response.session.access_token,
                        response.session.refresh_token,
                    )
                    st.rerun()
                else:
                    st.warning("Please confirm your email before signing in.")

            except Exception as e:
                st.error(f"Sign in failed: {e}")

    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input(
                "Password",
                type="password",
                key="signup_password",
            )

            signup_button = st.form_submit_button("Create Account")

        if signup_button:
            try:
                response = sign_up(new_email, new_password)

                if response.user:
                    st.success(
                        "Account created! Please confirm your email "
                        "if required, then sign in."
                    )
                else:
                    st.info("Please check your email for confirmation.")

            except Exception as e:
                st.error(f"Sign up failed: {e}")

else:
    # Verify the session before allowing database access.
    try:
        client = st.session_state.supabase_client
        session = client.auth.get_session() if client else None

        if not session:
            raise ValueError("No active session")

        verified = client.auth.get_user(session.access_token)

        if not verified.user:
            raise ValueError("Invalid user session")

    except Exception:
        st.session_state.user = None
        st.session_state.supabase_client = None
        st.warning("Your session has expired. Please sign in again.")
        st.stop()

    st.success(f"Signed in as {verified.user.email}")

    # Load saved answers once per authenticated user.
    if st.session_state.get("answers_user_id") != verified.user.id:
        try:
            saved_answers = load_answers(client, verified.user.id)

            for question in get_questions():
                question_id = question["id"]
                st.session_state[f"sql_question_{question_id}"] = saved_answers.get(
                    question_id, ""
                )

            st.session_state.answers_user_id = verified.user.id

        except Exception as e:
            st.error(f"Could not load saved answers: {e}")
            st.stop()

    if st.button("Sign Out"):
        client.auth.sign_out()

        # Clear authentication state
        st.session_state.user = None
        st.session_state.supabase_client = None

        # Clear cached answer state
        st.session_state.pop("answers_user_id", None)

        # Clear SQL editor values
        for question in get_questions():
            st.session_state.pop(
                f"sql_question_{question['id']}",
                None,
            )

        st.rerun()

    st.divider()

    st.header("SQL Quiz Dashboard")
    st.write(
        f"Complete {len(get_questions())} SQL questions "
        f"for a total of {get_total_points()} points."
    )

    questions = get_questions()

    question_titles = {
        q["id"]: f"Question {q['id']}: {q['title']} " f"({q['points']} points)"
        for q in questions
    }

    selected_id = st.selectbox(
        "Select a question",
        options=list(question_titles.keys()),
        format_func=lambda qid: question_titles[qid],
    )

    question = next(q for q in questions if q["id"] == selected_id)

    st.subheader(question["title"])
    st.write(question["description"])

    sql = st.text_area(
        "Write your SQL query",
        height=180,
        placeholder="SELECT ...",
        key=f"sql_question_{selected_id}",
    )

    if st.button("Save Answer"):
        if not sql.strip():
            st.warning("Please write some SQL before saving.")
        else:
            try:
                save_answer(
                    client=client,
                    user_id=verified.user.id,
                    question_id=selected_id,
                    sql_answer=sql,
                )
                st.success("Answer saved successfully!")

            except Exception as e:
                st.error(f"Failed to save answer: {e}")

    if st.button("Run Query", type="primary"):
        if not sql.strip():
            st.warning("Please enter a SQL query.")
        else:
            try:
                # Only allow a single SELECT or WITH query.
                from psycopg import sql as psycopg_sql

                query_text = sql.strip()

                if not query_text.lower().startswith(
                    ("select ", "select\n", "with ", "with\n")
                ):
                    st.error("Only SELECT queries are allowed.")

                elif query_text.rstrip(";").count(";") > 0:
                    st.error("Only one SQL statement is allowed.")

                else:
                    result = run_query(query_text)

                    st.success(
                        f"Query executed successfully! " f"{len(result)} rows returned."
                    )

                    st.dataframe(
                        result,
                        use_container_width=True,
                        hide_index=True,
                    )

            except Exception as e:
                st.error(f"Query failed: {e}")
