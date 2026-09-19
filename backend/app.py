from dbm import sqlite3
from pika.spec import methods
from werkzeug.wsgi import responder
import os
import requests
from flask import Flask, render_template, request

# Initialize the Flask application
app = Flask(__name__, template_folder=os.path.abspath("../frontend/templates"))

# Define a route for the homepage
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keywords = request.form.get('keyword')
        return 'waow it work'

    url = "https://api.hirebase.org/v2/jobs/search"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "hb_d49dd728-6be9-4757-89bd-6a850ea41c2c",
    }
    body = {
        "job_titles": ["Software Engineer"],
        "keywords": ["Python"],
        "limit": 10,
        "job_types": ["Internship"],
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    return data

connect = sqlite3.connect('database.db')

# Run the application
if __name__ == '__main__':
    app.run(debug=True)