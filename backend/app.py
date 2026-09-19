import sqlite3
from werkzeug.wsgi import responder
import os
from flask import render_template, request, Flask
import requests


# Initialize the Flask application
app = Flask(__name__, template_folder=os.path.abspath("../frontend/templates"))

# Define a route for the homepage
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keywords')

    url = "https://api.hirebase.org/v2/jobs/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "hb_d49dd728-6be9-4757-89bd-6a850ea41c2c",
    }
    body = {
        "job_titles": ["Software Engineer"],
        "keywords": [keyword],
        "limit": 10,
        "job_types": ["Internship"],
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    return data

connect = sqlite3.connect('majors.db')
connect.execute('''
    CREATE TABLE IF NOT EXISTS Majors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    degree TEXT NOT NULL,
    course_name TEXT NOT NULL
    )
    ''')

connect2 = sqlite3.connect('courses.db')
connect2.execute('''
    CREATE TABLE IF NOT EXISTS Courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL,
    keywords TEXT NOT NULL
    )
    ''')

#################################
#probably don't need this
@app.route('/join', methods=['POST'])
def join():
    major = request.form.get('major', '').strip()
    course_name = request.form.get('course', '').strip()

    if not major and not course_name:
        return render_template(
            "index.html",
            message="Please enter a major or a course."
        )

    with sqlite3.connect("majors.db") as db:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO Classes (major, course) VALUES (?, ?)",
            (major or None, course_name or None)
        )
        db.commit()

    return render_template(
        "index.html"    )
#################################

# Run the application
if __name__ == '__main__':
    app.run(debug=True)