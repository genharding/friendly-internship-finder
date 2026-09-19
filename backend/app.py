import os
from flask import render_template
from flask import Flask

# Initialize the Flask application
app = Flask(__name__, template_folder=os.path.abspath("../internship-searcher-other/templates"))

# Define a route for the homepage
@app.route('/')
def home():
    return render_template("index.html")

# Run the application
if __name__ == '__main__':
    app.run(debug=True)