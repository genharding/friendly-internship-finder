import json
import sqlite3
import sys
import time

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

BATCH_SIZE = 25
MODEL = "openai/gpt-oss-120b"

PROMPT_TEMPLATE = """You generate short skill/topic keyword tags for university courses,
to help match students to relevant internships based on coursework.

For each course below, produce 3-5 lowercase, comma-free keywords describing the
skills/topics a student would gain (e.g. "python", "financial accounting",
"circuit design", "statistics"). Keep each keyword 1-3 words.

Courses:
{course_list}

Respond with ONLY a JSON object mapping each course code to an array of keyword
strings, like:
{{"CS 1014": ["python", "algorithms", "problem solving"], "ACIS 1004": ["accounting basics", "bookkeeping"]}}
"""


def get_unenriched_courses(courses_conn, majors_conn, limit=None):
    rows = courses_conn.execute(
        "SELECT id, course_name FROM Courses WHERE keywords = '' OR keywords IS NULL"
    ).fetchall()
    if limit:
        rows = rows[:limit]

    # Look up a fuller display title (with course name text) from Majors when available,
    # since Courses.course_name is often just a bare code like "ACIS 1004".
    titles = {}
    for course_id, code in rows:
        match = majors_conn.execute(
            "SELECT course_name FROM Majors WHERE course_name LIKE ? LIMIT 1",
            (f"{code}%",),
        ).fetchone()
        titles[course_id] = match[0] if match else code

    return [(course_id, code, titles[course_id]) for course_id, code in rows]


def enrich_batch(llm, batch):
    course_list = "\n".join(f"- {code}: {title}" for _, code, title in batch)
    prompt = PROMPT_TEMPLATE.format(course_list=course_list)

    response = llm.invoke(prompt)
    text = response.content.strip()

    # Models sometimes wrap JSON in a code fence despite instructions.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print(f"    [!] Could not parse model response as JSON, skipping batch:\n{text[:300]}")
        return {}


def main(limit=None):
    llm = ChatGroq(model=MODEL, temperature=0)

    with sqlite3.connect("courses.db") as courses_conn, sqlite3.connect(
        "majors.db"
    ) as majors_conn:
        pending = get_unenriched_courses(courses_conn, majors_conn, limit=limit)
        print(f"[*] {len(pending)} courses need keywords.")

        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i : i + BATCH_SIZE]
            print(f"    -> Enriching batch {i // BATCH_SIZE + 1} ({len(batch)} courses)...")

            try:
                keyword_map = enrich_batch(llm, batch)
            except Exception as e:
                print(f"    [!] Groq call failed: {e}")
                continue

            for course_id, code, _title in batch:
                keywords = keyword_map.get(code)
                if not keywords:
                    continue
                courses_conn.execute(
                    "UPDATE Courses SET keywords = ? WHERE id = ?",
                    (", ".join(keywords), course_id),
                )
            courses_conn.commit()

            time.sleep(0.5)

    print("[+] Done.")


if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(limit=limit_arg)
