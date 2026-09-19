import json
import os
import re
import sqlite3

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_groq import ChatGroq

load_dotenv()

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
HIREBASE_API_KEY = os.environ.get("HIREBASE_API_KEY")

app = Flask(__name__, template_folder=os.path.abspath("../frontend/templates"))


def db_path(name):
    return os.path.join(BACKEND_DIR, name)


def ensure_schema():
    with sqlite3.connect(db_path("majors.db")) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS Majors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                degree TEXT NOT NULL,
                course_name TEXT NOT NULL
            )
            """
        )
    with sqlite3.connect(db_path("courses.db")) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS Courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                keywords TEXT NOT NULL
            )
            """
        )


ensure_schema()


@app.route("/")
def home():
    with sqlite3.connect(db_path("majors.db")) as db:
        majors = [
            row[0]
            for row in db.execute("SELECT DISTINCT degree FROM Majors ORDER BY degree")
        ]
    return render_template("index.html", majors=majors)


@app.route("/courses")
def courses_for_major():
    major = request.args.get("major", "")
    with sqlite3.connect(db_path("majors.db")) as db:
        rows = db.execute(
            "SELECT DISTINCT course_name FROM Majors WHERE degree = ? ORDER BY course_name",
            (major,),
        ).fetchall()
    return jsonify({"courses": [r[0] for r in rows]})


@tool
def get_skills_for_courses(course_codes: str) -> str:
    """Given a comma-separated list of course codes (e.g. 'CS 1014, MATH 1225'),
    look up their skill/topic keywords from the courses database. Returns a JSON
    object mapping course code to a keyword string."""
    codes = [c.strip() for c in course_codes.split(",") if c.strip()]
    results = {}
    with sqlite3.connect(db_path("courses.db")) as db:
        for code in codes:
            row = db.execute(
                "SELECT keywords FROM Courses WHERE course_name = ?", (code,)
            ).fetchone()
            if row and row[0]:
                results[code] = row[0]
    return json.dumps(results)


# Populated by search_internships with the untruncated job data, keyed by
# application_link, so /recommend can restore full descriptions after the
# agent (which only sees a truncated version to stay under Groq's token limit)
# returns its picks.
_last_search_results = {}


def _strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "")


@tool
def search_internships(job_titles: str, keywords: str) -> str:
    """Search for internships via the Hirebase API. job_titles and keywords are
    each comma-separated strings, e.g. 'Software Engineer, Backend Developer'.
    Returns a JSON array of job objects, or a JSON object with an 'error' key."""
    url = "https://api.hirebase.org/v2/jobs/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": HIREBASE_API_KEY,
    }
    title_list = [t.strip() for t in job_titles.split(",") if t.strip()]
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    body = {
        "job_titles": title_list or ["Software Engineer"],
        "keywords": keyword_list,
        "limit": 10,
        "job_types": ["Internship"],
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        jobs = response.json().get("jobs", [])
    except requests.RequestException as e:
        return json.dumps({"error": str(e)})

    _last_search_results.clear()
    trimmed_jobs = []
    for job in jobs:
        link = job.get("application_link", "")
        _last_search_results[link] = job
        trimmed = dict(job)
        trimmed["description"] = _strip_html(job.get("description", ""))[:300]
        trimmed_jobs.append(trimmed)

    return json.dumps(trimmed_jobs)


AGENT_SYSTEM_PROMPT = """You are a campus career navigator agent. Given a student's
major, courses taken, and interests, you:

1. Call get_skills_for_courses with their course codes to find relevant skills.
2. Based on their major, those skills, and their interests, decide relevant
   job_titles and keywords for an internship search.
3. Call search_internships with those job_titles/keywords.
4. From the jobs search_internships returns, pick the best matches and respond
   with ONLY a JSON array (no other text), where each item has exactly these
   fields: job_title, company_name, company_logo, company_link, description,
   application_link, rationale.

Use the exact values from the tool output for every field except "rationale" -
never invent job data. "rationale" should be 1-2 sentences on why this specific
role fits this student, referencing their coursework or interests.

If search_internships returns no jobs or an error, respond with exactly: []
"""

# The 20b variant has a much higher free-tier tokens-per-minute limit than the
# 120b model -- important for a tool-calling agent whose context includes real
# API responses.
_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
_agent_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", AGENT_SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)
_agent = create_tool_calling_agent(
    _llm, [get_skills_for_courses, search_internships], _agent_prompt
)
agent_executor = AgentExecutor(
    agent=_agent,
    tools=[get_skills_for_courses, search_internships],
    verbose=True,
)


def parse_agent_output(raw_output: str):
    text = raw_output.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


@app.route("/recommend", methods=["POST"])
def recommend():
    major = request.form.get("major", "")
    selected_courses = request.form.getlist("courses")
    interests = request.form.get("interests", "")

    course_codes = ", ".join(c.split(" - ")[0].strip() for c in selected_courses)

    user_request = (
        f"Student major: {major}\n"
        f"Courses taken: {course_codes or 'none provided'}\n"
        f"Interests: {interests or 'none provided'}\n"
        "Find and explain the best-matching internships for this student."
    )

    try:
        result = agent_executor.invoke({"input": user_request})
        jobs = parse_agent_output(result["output"])
    except Exception as e:
        return render_template(
            "listings.html",
            jobs=[],
            error=f"Something went wrong finding matches: {e}",
        )

    # The agent only saw truncated descriptions (to stay under the Groq token
    # limit); restore the full original text for display.
    for job in jobs:
        original = _last_search_results.get(job.get("application_link"))
        if original:
            job["description"] = original.get("description", job.get("description"))

    return render_template("listings.html", jobs=jobs, error=None)


if __name__ == "__main__":
    app.run(debug=True)
