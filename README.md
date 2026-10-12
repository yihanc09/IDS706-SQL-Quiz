[![SQL Quiz CI](https://github.com/yihanc09/IDS706-SQL-Quiz/actions/workflows/test.yml/badge.svg)](https://github.com/yihanc09/IDS706-SQL-Quiz/actions/workflows/test.yml)

# IDS706 SQL Quiz

A deployed, authentication-protected & interactive SQL quiz application built with Streamlit, Supabase PostgreSQL, and Python for IDS706 Data Engineering.

Students can practice SQL against the Chinook Music Store database, execute read-only queries, view real query results, receive automatic grading feedback, and save their answers across login sessions.

## Live Application

**Streamlit App:** [Open SQL Quiz](https://ids706-sql-quiz.streamlit.app/)

## Project Overview

This project provides an interactive SQL learning environment backed by a hosted PostgreSQL database.

The application includes five SQL questions worth a total of 20 points. Each question has a reference SQL query and an expected result generated from the Chinook database.

### Key Features

- **User Authentication:** Sign up, sign in, and sign out using Supabase Authentication.
- **Dataset Guide:** Introduces the Chinook music store database, its key tables, and their relationships.
- **Contextual Learning Support:** Each question includes a business scenario and an expandable reference to relevant tables and fields, helping students unfamiliar with the dataset complete the quiz.
- **Interactive SQL Editor:** Write and execute SQL queries through the Streamlit interface.
- **Real Database Results:** Display query output directly from hosted PostgreSQL.
- **Automatic Grading:** SQL query results are compared against expected results, with four points available per question.
- **Persistent Progress:** Save SQL answers to Supabase and restore them after signing in again.
- **Results Dashboard:** Displays individual question scores, completion status, and total points earned.
- **Access Control:** Require authentication before accessing the quiz.
- **Read-Only Query Execution:** Use a restricted PostgreSQL role and read-only transactions.
- **Automated Testing:** Validate quiz content, database connectivity, and selected SQL security scenarios.
- **Continuous Integration:** Automatically run tests through GitHub Actions.

## Technology Stack

| Component | Technology |
|---|---|
| Web application | Streamlit |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Database driver | psycopg |
| Data processing | pandas |
| Testing | pytest |
| Continuous Integration | GitHub Actions |
| Deployment | Streamlit Community Cloud |

## Quiz Content

The quiz contains five questions, each worth four points.

| Question | Topic | Points |
|---|---|---:|
| 1 | Count all artists | 4 |
| 2 | Top five artists by album count | 4 |
| 3 | Average track duration by genre | 4 |
| 4 | Top five customers by total spending | 4 |
| 5 | Top five genres by tracks sold | 4 |
| **Total** | | **20** |

The quiz uses the Chinook Music Store database, with tables including `artist`, `album`, `genre`, `track`, `customer`, `invoice`, and `invoice_line`.

Reference SQL queries are defined in `quiz.py`. Their generated results are stored in `data/expected_results.json`.

## Application Workflow

1. Open the deployed Streamlit application.
2. Create an account or sign in.
3. Select a SQL question.
4. Write a query in the SQL editor.
5. Click **Run Query** to execute the SQL and display the resulting table.
6. Click **Save Answer** to store the SQL answer in Supabase.
7. Sign out and sign in again to retrieve previously saved answers.

Unauthenticated visitors can access the sign-in and sign-up interface but cannot execute SQL queries or save answers.

## Database and Security

The application uses a hosted Supabase PostgreSQL database.

Chinook tables are stored in the `chinook` schema. Saved student answers are stored separately in `public.quiz_answers`.

Security measures include:

- Supabase Authentication for user access.
- Row Level Security (RLS) policies restricting access to each user's saved answers.
- A dedicated `quiz_reader` PostgreSQL role for query execution.
- Read-only database transactions.
- A statement timeout and result-row limit.
- Credentials stored in environment variables, Streamlit Secrets, and GitHub Actions Secrets rather than committed source code.

The SQL security tests cover selected cases, including attempts to create, update, or delete records, execute multiple statements, and read saved student answers through the quiz database connection.

These checks provide defense in depth but are not a comprehensive security audit.

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yihanc09/IDS706-SQL-Quiz.git
cd IDS706-SQL-Quiz
```

### 2. Install Dependencies

Python 3.12 is recommended.

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a local `.env` file with:

```dotenv
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_publishable_or_anon_key
QUIZ_DATABASE_URL=your_read_only_postgresql_connection_string
```

The `.env` file is excluded from version control.

Use the restricted `quiz_reader` connection string for `QUIZ_DATABASE_URL`. Do not use a database administrator connection for student-submitted SQL.

### 4. Run the Application

```bash
python -m streamlit run app.py
```

Open the local URL displayed in the terminal, typically `http://localhost:8501`.

## Testing

The project uses pytest and includes 14 automated tests.

| Test Category | Tests |
|---|---:|
| Quiz content and expected results | 7 |
| PostgreSQL connection | 1 |
| SQL security checks | 6 |
| **Total** | **14** |

Run all tests locally:

```bash
python -m pytest -v
```

Database-dependent tests require a valid `QUIZ_DATABASE_URL`.

### GitHub Actions

The CI workflow is defined in `.github/workflows/test.yml`.

It runs automatically on pushes and pull requests targeting `main` and can also be triggered manually.

The workflow contains two jobs:

- **unit-tests:** Runs seven tests without requiring a database connection.
- **database-tests:** Runs seven integration and security tests using the `QUIZ_DATABASE_URL` GitHub Actions Secret.

**Verified CI result:** Both jobs completed successfully, with all 14 tests passing.

## Production Smoke Test

After deployment to Streamlit Community Cloud, the following actions were manually verified:

| Test | Result |
|---|---|
| Sign in with an existing account | Passed |
| Execute Question 1 and return 275 artists | Passed |
| Save an SQL answer | Passed |
| Sign out, sign in, and restore the saved SQL | Passed |
| Prevent logged-out users from executing or saving SQL | Passed |

**Result:** All five production smoke-test checks passed.


### Audit Logging

The application uses a PostgreSQL audit table and an
AFTER INSERT OR UPDATE trigger on `public.quiz_answers`.

Each audit record includes:
- The authenticated user's ID
- The action performed (SAVE_ANSWER or UPDATE_ANSWER)
- The question ID
- The timestamp

Audit records are generated automatically by PostgreSQL
when a student's answer is inserted or updated.

### Audit Log Integrity

The audit log is protected using PostgreSQL permissions
and Row Level Security (RLS).

- The `quiz_reader` role cannot read or modify audit records.
- The `authenticated` role has no direct table access.
- A SECURITY DEFINER trigger function writes audit records.
- Direct DELETE attempts using the student database role
  are rejected.

Database privilege checks and a negative DELETE test
were performed to verify the access restrictions.

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
│   ├── test_database_connection.py
│   └── test_sql_security.py
├── app.py
├── auth.py
├── database.py
├── quiz.py
├── generate_expected_results.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Current Scope

The application supports SQL execution, result visualization, authentication, and persistent answer storage.

Each question is assigned four possible points, but the application does not currently calculate or award grades automatically. Reference results are used for documentation and automated testing.

Because the repository is public, reference SQL and expected results stored in the repository should not be treated as confidential grading material.