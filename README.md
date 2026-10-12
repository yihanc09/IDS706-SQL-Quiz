[![SQL Quiz CI](https://github.com/yihanc09/IDS706-SQL-Quiz/actions/workflows/test.yml/badge.svg)](https://github.com/yihanc09/IDS706-SQL-Quiz/actions/workflows/test.yml)

# IDS706 SQL Quiz

An interactive, authentication-protected SQL quiz built with **Streamlit, Supabase PostgreSQL, and Python** for IDS706 Data Engineering. Students explore the Chinook Music Store database, run read-only SQL queries, receive automatic grading feedback, and resume their work across sessions.

**Live app:** [Launch IDS706 SQL Quiz](https://ids706-sql-quiz.streamlit.app/)

## Project Overview

The quiz includes **five business-oriented SQL questions worth 20 points total**. Each question is graded against reference results generated from the Chinook database. Students can navigate between questions, save drafts, submit answers for grading, and review their scores in a Results Dashboard.

### Key Features

- **Authentication:** Sign up, sign in, and sign out with Supabase Auth.
- **Dataset guide:** Introduces the Chinook tables, fields, and relationships; a database reference remains available in the sidebar.
- **Contextual questions:** Business scenarios and relevant-table hints accompany each exercise.
- **Interactive SQL execution:** Run read-only queries and inspect returned PostgreSQL results.
- **Automatic grading:** Compare query results with stored reference results; each question earns 0 or 4 points.
- **Persistent answers and grades:** Save drafts and graded submissions in Supabase; restore them after signing in again.
- **Results Dashboard:** View per-question status, scores, and the total out of 20.
- **Security controls:** Restricted query role, read-only transactions, RLS for student answers, and audit logging.
- **Automated testing and CI:** pytest tests run locally and through GitHub Actions.

## Technology Stack

| Component | Technology |
|---|---|
| Web application | Streamlit |
| Hosted database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| PostgreSQL driver | psycopg |
| Data processing | pandas |
| Testing | pytest |
| Continuous integration | GitHub Actions |
| Deployment | Streamlit Community Cloud |

## Quiz Content

| Question | Topic | Points |
|---|---|---:|
| 1 | Count all artists | 4 |
| 2 | Top five artists by album count | 4 |
| 3 | Average track duration by genre | 4 |
| 4 | Top five customers by total spending | 4 |
| 5 | Top five genres by tracks sold | 4 |
| **Total** | | **20** |

The quiz uses the `chinook` schema, including `artist`, `album`, `genre`, `track`, `customer`, `invoice`, and `invoice_line`. Question definitions and reference SQL are in `quiz.py`; expected outputs are in `data/expected_results.json`.

## Application Workflow

1. Open the [deployed app](https://ids706-sql-quiz.streamlit.app/) and sign up or sign in.
2. Read the **Welcome & Dataset Guide** and choose a question.
3. Write SQL in the editor; select **Run Query** to inspect the results.
4. Select **Save Answer** to preserve a draft, or **Submit for Grading** to evaluate and persist the answer and score.
5. Navigate between questions and open **Quiz Results** to review progress and the total score.
6. Sign out and sign back in to restore saved answers and grades.

Unauthenticated visitors can access the sign-in/sign-up screen but cannot run quiz queries or save answers. Submitting a revised answer updates that question's saved grade; the quiz does not permanently lock submissions.

## Database and Security

Chinook data is stored in the `chinook` schema. Per-user SQL answers and grades are stored in `public.quiz_answers`, with Supabase Row Level Security (RLS) restricting access to the corresponding authenticated user.

Student SQL runs through the restricted `quiz_reader` PostgreSQL connection rather than an administrator account. Query execution uses a **read-only transaction**, a **10-second statement timeout**, and a **500-row result limit**. The application also checks for a single SELECT/CTE-style statement before execution. These are layered safeguards, not a complete SQL sandbox or security audit.

Credentials are configured through environment variables, Streamlit Secrets, and GitHub Actions Secrets; they are not committed to the repository. Never use an administrator database URL for `QUIZ_DATABASE_URL`.

### Optional Extra Credit: Audit Logging and Integrity

The application tracks quiz activity in `public.quiz_audit_log`:

| Event | How it is recorded |
|---|---|
| `SAVE_ANSWER` / `UPDATE_ANSWER` | PostgreSQL `AFTER INSERT OR UPDATE` trigger on `public.quiz_answers` |
| `RUN_QUERY` | Application invokes an authenticated audit RPC when a student runs SQL |
| `SUBMIT_QUERY` | Application invokes the audit RPC when SQL is executed for grading |

Audit entries include the user ID, action, question ID, timestamp, and execution status where applicable. The log records activity metadata rather than the full submitted SQL text.

**Integrity controls:** The audit table uses RLS and PostgreSQL permissions. Neither `quiz_reader` nor `authenticated` has direct table access. A `SECURITY DEFINER` trigger records answer changes; direct execution permission on that trigger function is revoked from student-facing roles. A restricted RPC handles query-execution events.

**Verification:** Manual privilege checks confirmed that both student-facing roles lack direct audit-table privileges. A DELETE attempt under `quiz_reader` was rejected. Audit entries appeared after saving answers, running queries, and submitting for grading. Automated security tests check table privileges, read restrictions, and trigger-function configuration.

**Limitations:** Authenticated users can potentially invoke the query-audit RPC to submit fabricated events. The audit table is protected against direct edits, but the query-event log is **not** cryptographically tamper-proof or authoritative proof of execution.

### SQL Parameterization and Injection Safety

The application does **not** interpolate student-provided values into application-generated SQL using Python f-strings. Students submit entire SQL statements, so a parameter placeholder cannot replace the complete statement. The restricted role and read-only transaction provide additional protection; they should not be confused with parameterization or a guarantee against every SQL-based attack.

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yihanc09/IDS706-SQL-Quiz.git
cd IDS706-SQL-Quiz
```

### 2. Install Dependencies

Python **3.12** is recommended (and used in CI).

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a local `.env` file (do not commit it):

```dotenv
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
QUIZ_DATABASE_URL=your_quiz_reader_postgresql_connection_string
```

Use a read-only `quiz_reader` connection string for `QUIZ_DATABASE_URL`. The Supabase project must already contain the Chinook tables, answer table, RLS policies, and audit functions; environment variables alone do not provision the database.

### 4. Run the Application

```bash
python -m streamlit run app.py
```

Open the local URL shown in the terminal (usually `http://localhost:8501`).

## Testing and Continuous Integration

The repository contains **33 pytest test cases** across four files (including five parameterized grading cases):

| Test file | Test cases | Coverage |
|---|---:|---|
| `tests/test_quiz.py` | 7 | Quiz structure and reference results |
| `tests/test_grading.py` | 8 | Correct results and incorrect-result edge cases |
| `tests/test_database_connection.py` | 1 | Live Chinook database connectivity |
| `tests/test_sql_security.py` | 17 | SQL restrictions and audit-log permissions |
| **Total** | **33** | |

Run the full local test suite:

```bash
python -m pytest -v
```

The database connection and security tests require a valid `QUIZ_DATABASE_URL` and a reachable Supabase PostgreSQL instance. The grading and quiz-content tests do not require a live database.

### GitHub Actions

The workflow is in `.github/workflows/test.yml` and runs on pushes and pull requests to `main`, or by manual dispatch. **With the current workflow configuration**, it executes:

- **`unit-tests`:** `tests/test_quiz.py` (7 cases).
- **`database-tests`:** `tests/test_database_connection.py` and `tests/test_sql_security.py` (18 cases), using the `QUIZ_DATABASE_URL` repository Secret.

This means CI is configured to run **25 test cases**. `tests/test_grading.py` is included in the local full-suite command but is **not yet included in the current CI workflow**. Add it to the unit-test command if you want CI to cover all 33 cases.

The 17 SQL security tests passed locally after tightening trigger-function permissions. Confirm the latest GitHub Actions run is green before reporting the updated CI as passing.

## Production Smoke Tests

The deployed Streamlit application has been manually checked for the following behaviors:

| Check | Result |
|---|---|
| Sign in and access the quiz | Passed |
| Run Question 1 and retrieve 275 artists | Passed |
| Save an answer and restore it after signing out and back in | Passed |
| Submit answers for automatic grading and review results | Passed |
| Restrict quiz access for logged-out visitors | Passed |
| Generate audit events for saving, running, and submitting SQL | Passed |
| Reject unauthorized audit-log deletion | Passed |

These are manual functional checks, not a substitute for comprehensive production security testing.

## Project Structure

```text
IDS706-SQL-Quiz/
├── .github/
│   └── workflows/
│       └── test.yml
├── data/
│   └── expected_results.json
├── tests/
│   ├── test_quiz.py
│   ├── test_grading.py
│   ├── test_database_connection.py
│   └── test_sql_security.py
├── app.py
├── auth.py
├── database.py
├── grading.py
├── quiz.py
├── generate_expected_results.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Scope and Limitations

This is an educational SQL practice application, not a high-stakes exam platform. Students receive automatic result-based grading and persistent scores, but submissions are not locked. Reference SQL and expected results are stored in the public repository, so they are not secret assessment materials. Query-event audit entries can be fabricated through the authenticated RPC and should not be treated as independently verified execution evidence.
