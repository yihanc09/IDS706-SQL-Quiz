"""IDS706 SQL quiz: per-question drafts, persistent grades, and navigation."""
import streamlit as st
from auth import get_supabase_client, sign_in, sign_up, save_answer, load_answer_records, save_graded_answer
from database import run_query
from grading import grade_result
from quiz import get_questions, get_total_points

st.set_page_config(page_title="IDS706 SQL Quiz", page_icon="🎓", layout="wide")
st.title("IDS706 SQL Quiz")
st.caption("Practice SQL with the Chinook Music Store Database")
QUESTIONS = get_questions()
BY_ID = {q["id"]: q for q in QUESTIONS}
IDS = list(BY_ID)


def reset_quiz_state():
    """Remove all user-specific state, including drafts and widget state."""
    for key in list(st.session_state):
        if key.startswith(("draft_", "editor_")) or key in (
            "loaded_user_id", "grades", "selected_question", "query_result", "query_question"
        ):
            st.session_state.pop(key, None)


def sync_editor():
    """Copy editor text into durable session state before Streamlit removes hidden widgets."""
    qid = st.session_state.selected_question
    st.session_state[f"draft_{qid}"] = st.session_state[f"editor_{qid}"]


def select_question(qid):
    st.session_state.selected_question = qid


st.session_state.setdefault("user", None)
st.session_state.setdefault("supabase_client", None)

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
                    reset_quiz_state()
                    st.session_state.user = response.user
                    client = get_supabase_client()
                    client.auth.set_session(response.session.access_token, response.session.refresh_token)
                    st.session_state.supabase_client = client
                    st.rerun()
                else:
                    st.warning("Please confirm your email before signing in.")
            except Exception as exc:
                st.error(f"Sign in failed: {exc}")
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            signup_button = st.form_submit_button("Create Account")
        if signup_button:
            try:
                response = sign_up(new_email, new_password)
                if response.user:
                    st.success("Account created! Confirm your email if required, then sign in.")
                else:
                    st.info("Please check your email for confirmation.")
            except Exception as exc:
                st.error(f"Sign up failed: {exc}")
else:
    try:
        client = st.session_state.supabase_client
        session = client.auth.get_session() if client else None
        if not session:
            raise ValueError("No active session")
        verified = client.auth.get_user(session.access_token)
        if not verified.user:
            raise ValueError("Invalid user session")
    except Exception:
        reset_quiz_state()
        st.session_state.user = None
        st.session_state.supabase_client = None
        st.warning("Your session has expired. Please sign in again.")
        st.stop()

    # Load all saved records only on login, never on every question change.
    if st.session_state.get("loaded_user_id") != verified.user.id:
        try:
            records = load_answer_records(client, verified.user.id)
        except Exception as exc:
            st.error(f"Could not load saved answers: {exc}")
            st.stop()
        reset_quiz_state()
        st.session_state.grades = {}
        for qid in IDS:
            record = records.get(qid, {})
            draft = record.get("sql_answer") or ""
            st.session_state[f"draft_{qid}"] = draft
            if record.get("score") is not None and record.get("is_correct") is not None:
                st.session_state.grades[qid] = {
                    "sql": draft,
                    "score": int(record["score"]),
                    "correct": bool(record["is_correct"]),
                }
        st.session_state.selected_question = IDS[0]
        st.session_state.loaded_user_id = verified.user.id

    st.success(f"Signed in as {verified.user.email}")
    if st.button("Sign Out"):
        try:
            client.auth.sign_out()
        finally:
            reset_quiz_state()
            st.session_state.user = None
            st.session_state.supabase_client = None
        st.rerun()

    st.divider()
    st.header("SQL Quiz Dashboard")
    st.write(f"Complete {len(QUESTIONS)} SQL questions for a total of {get_total_points()} points.")
    grades = st.session_state.grades
    # Only the grade for an edited question becomes stale. Other questions retain their grades.
    for qid in IDS:
        saved_grade = grades.get(qid)
        if saved_grade and saved_grade["sql"] != st.session_state.get(f"draft_{qid}", ""):
            grades.pop(qid, None)
    earned = sum(entry["score"] for entry in grades.values())
    st.metric("Total graded score", f"{earned} / {get_total_points()}")
    st.caption("Scores are saved when you submit for grading. Unsaved edits are drafts, not submitted grades.")

    # Results is a separate final page; grades remain keyed by question ID.
    RESULTS_PAGE = "results"
    pages = IDS + [RESULTS_PAGE]
    labels = {qid: f"Question {qid}: {BY_ID[qid]['title']} ({BY_ID[qid]['points']} points)" for qid in IDS}
    labels[RESULTS_PAGE] = "Quiz Results"
    selected_id = st.selectbox(
        "Select a page", pages, key="selected_question", format_func=lambda page: labels[page]
    )
    pos = pages.index(selected_id)
    left, right = st.columns(2)
    left.button("← Previous Question" if selected_id != RESULTS_PAGE else "← Review Question 5",
                disabled=pos == 0, on_click=select_question,
                args=(pages[max(0, pos - 1)],), use_container_width=True)
    right.button("View Results →" if pos == len(IDS) - 1 else "Next Question →",
                 disabled=pos == len(pages) - 1, on_click=select_question,
                 args=(pages[min(len(pages) - 1, pos + 1)],), use_container_width=True)

    if selected_id == RESULTS_PAGE:
        st.subheader("SQL Quiz Results")
        graded_count = len(grades)
        st.write(f"Graded questions: {graded_count} / {len(QUESTIONS)}")
        st.metric("Total Score", f"{earned} / {get_total_points()}")
        if graded_count == len(QUESTIONS):
            st.success("All five questions have been graded! You can review or revise your answers.")
        else:
            st.info("You can view results at any time. Unsubmitted questions are marked Not graded.")

        result_rows = []
        for qid in IDS:
            item = BY_ID[qid]
            grade = grades.get(qid)
            result_rows.append({
                "Question": f"Q{qid}: {item['title']}",
                "Status": "Correct" if grade and grade["correct"] else ("Incorrect" if grade else "Not graded"),
                "Score": f"{grade['score'] if grade else 0} / {item['points']}",
            })
        st.dataframe(result_rows, use_container_width=True, hide_index=True)
        st.caption("Finish & Sign Out ends your session; it does not lock your answers or grades.")
        review_col, finish_col = st.columns(2)
        review_col.button("Review Answers", on_click=select_question, args=(IDS[0],),
                          use_container_width=True)
        if finish_col.button("Finish & Sign Out", type="primary", use_container_width=True):
            try:
                client.auth.sign_out()
            finally:
                reset_quiz_state()
                st.session_state.user = None
                st.session_state.supabase_client = None
            st.rerun()
    else:
        question = BY_ID[selected_id]
        st.subheader(question["title"])
        st.write(question["description"])
        editor_key = f"editor_{selected_id}"
        draft_key = f"draft_{selected_id}"
        # Streamlit deletes widget keys when widgets disappear. Restore from durable draft key.
        if editor_key not in st.session_state:
            st.session_state[editor_key] = st.session_state.get(draft_key, "")
        st.text_area("Write your SQL query", height=180, placeholder="SELECT ...",
                     key=editor_key, on_change=sync_editor)
        sql = st.session_state[draft_key]

        if st.button("Save Answer"):
            if not sql.strip():
                st.warning("Please write some SQL before saving.")
            else:
                try:
                    # Saving an unchanged, already-graded SQL must not erase its grade.
                    existing = grades.get(selected_id)
                    if existing and existing["sql"] == sql:
                        st.info("This answer is already saved and graded; your score is unchanged.")
                    else:
                        save_answer(client, verified.user.id, selected_id, sql)
                        grades.pop(selected_id, None)
                        st.success("Draft saved! Submit for grading when ready.")
                except Exception as exc:
                    st.error(f"Failed to save answer: {exc}")

        col_run, col_submit = st.columns(2)
        run_clicked = col_run.button("Run Query", use_container_width=True)
        submit_clicked = col_submit.button("Submit for Grading", type="primary", use_container_width=True)
        if run_clicked or submit_clicked:
            query_text = sql.strip()
            if not query_text:
                st.warning("Please enter a SQL query.")
            elif not query_text.lower().startswith(("select ", "select\n", "with ", "with\n")):
                st.error("Only SELECT queries are allowed.")
            elif query_text.rstrip(";").count(";") > 0:
                st.error("Only one SQL statement is allowed.")
            else:
                try:
                    result = run_query(query_text)
                    st.success(f"Query executed successfully! {len(result)} rows returned.")
                    st.dataframe(result, use_container_width=True, hide_index=True)
                    if submit_clicked:
                        correct, feedback = grade_result(selected_id, result)
                        points = question["points"] if correct else 0
                        save_graded_answer(client, verified.user.id, selected_id, sql, points, correct)
                        grades[selected_id] = {"sql": sql, "correct": correct, "score": points}
                        if correct:
                            st.success(f"Correct! {points} / {question['points']} points. {feedback}")
                        else:
                            st.warning(f"Not yet correct: 0 / {question['points']} points. {feedback}")
                        st.info(f"Updated total score: {sum(g['score'] for g in grades.values())} / {get_total_points()}")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Query or grade submission failed: {exc}")

        grade = grades.get(selected_id)
        if grade and grade["sql"] == sql:
            if grade["correct"]:
                st.success(f"Saved grade: Correct — {grade['score']} / {question['points']} points")
            else:
                st.warning(f"Saved grade: Not yet correct — 0 / {question['points']} points")
