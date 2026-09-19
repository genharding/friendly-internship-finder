import io
import re
import sqlite3
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

# Windows terminals default to cp1252, which can't encode characters
# (e.g. zero-width spaces) that show up in scraped subject names.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://catalog.vt.edu/course-descriptions/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
REQUEST_DELAY_SECONDS = 0.4


def check_robots_allowed(url: str) -> bool:
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(url, "/robots.txt"))
    try:
        rp.read()
    except Exception:
        # If robots.txt can't be fetched, don't block a run over it.
        return True
    return rp.can_fetch(USER_AGENT, url)


ZERO_WIDTH_SPACE = chr(0x200B)


def sanitize_text(text: str) -> str:
    cleaned = text.replace(ZERO_WIDTH_SPACE, "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def get_subject_links(page) -> list[tuple[str, str]]:
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_selector("a[href*='/course-descriptions/']", timeout=15000)

    raw_links = page.eval_on_selector_all(
        "a[href*='/course-descriptions/']",
        "els => els.map(e => [e.textContent.trim(), e.getAttribute('href')])",
    )

    subject_links = []
    seen = set()
    for text, href in raw_links:
        if not text or href in (None, "/course-descriptions/", "#"):
            continue
        full_url = urljoin(BASE_URL, href)
        if full_url in seen:
            continue
        seen.add(full_url)
        subject_links.append((sanitize_text(text), full_url))

    return subject_links


def scrape_subject_courses(page, subject_url: str) -> list[dict]:
    page.goto(subject_url, wait_until="networkidle", timeout=30000)
    try:
        page.wait_for_selector(".courseblock", timeout=8000)
    except Exception:
        # Some subject pages legitimately have zero courses listed.
        return []

    blocks = page.eval_on_selector_all(
        ".courseblock",
        """
        els => els.map(e => {
            const code = e.querySelector('.detail-code');
            const title = e.querySelector('.detail-title');
            const credits = e.querySelector('.detail-hours_html');
            const desc = e.querySelector('.courseblockextra');
            return {
                code: code ? code.textContent.trim() : '',
                title: title ? title.textContent.replace(/^-\\s*/, '').trim() : '',
                credits: credits ? credits.textContent.trim() : '',
                description: desc ? desc.textContent.trim() : ''
            };
        })
        """,
    )

    courses = []
    for b in blocks:
        code = sanitize_text(b["code"])
        if not code:
            continue
        title = sanitize_text(b["title"])
        credits = sanitize_text(b["credits"])
        description = sanitize_text(b["description"])
        display = f"{code} - {title} {credits}".strip() if title else code
        courses.append(
            {
                "code": code,
                "title": title,
                "display": display,
                "description": description,
            }
        )
    return courses


def scrape_all_vt_majors(subject_limit: int | None = None) -> list[dict]:
    print(f"[*] Fetching subject index from {BASE_URL}...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)

        subject_links = get_subject_links(page)
        print(f"[+] Found {len(subject_links)} subject streams.")

        if subject_limit:
            subject_links = subject_links[:subject_limit]
            print(f"[*] Limiting this run to the first {subject_limit} subjects.")

        scraped_data_list = []
        for subject_name, subject_url in subject_links:
            print(f"    -> Scraping: {subject_name}")
            try:
                courses = scrape_subject_courses(page, subject_url)
                for course in courses:
                    scraped_data_list.append(
                        {"major": subject_name, **course}
                    )
                print(f"       {len(courses)} courses found")
            except Exception as e:
                print(f"    [!] Error scraping {subject_name}: {e}")

            time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    return scraped_data_list


def ensure_schema(majors_conn, courses_conn):
    majors_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Majors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            degree TEXT NOT NULL,
            course_name TEXT NOT NULL
        )
        """
    )
    courses_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            keywords TEXT NOT NULL
        )
        """
    )


def save_to_databases(scraped_items: list[dict]):
    with sqlite3.connect("majors.db") as majors_conn, sqlite3.connect(
        "courses.db"
    ) as courses_conn:
        ensure_schema(majors_conn, courses_conn)

        existing_codes = {
            row[0]
            for row in courses_conn.execute("SELECT course_name FROM Courses")
        }

        majors_rows = [(item["major"], item["display"]) for item in scraped_items]
        majors_conn.executemany(
            "INSERT INTO Majors (degree, course_name) VALUES (?, ?)", majors_rows
        )
        majors_conn.commit()

        new_codes = []
        seen_codes = set()
        for item in scraped_items:
            code = item["code"]
            if code and code not in existing_codes and code not in seen_codes:
                seen_codes.add(code)
                new_codes.append((code, ""))

        if new_codes:
            courses_conn.executemany(
                "INSERT INTO Courses (course_name, keywords) VALUES (?, ?)",
                new_codes,
            )
            courses_conn.commit()

        print(
            f"[+] Inserted {len(majors_rows)} Majors rows and "
            f"{len(new_codes)} new Courses rows (keywords left blank for enrichment)."
        )


if __name__ == "__main__":
    if not check_robots_allowed(BASE_URL):
        print(f"[!] robots.txt disallows fetching {BASE_URL}. Aborting.")
        sys.exit(1)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    items = scrape_all_vt_majors(subject_limit=limit)
    print(f"\n[+] Scraper complete. Found {len(items)} course records.")

    save_to_databases(items)
