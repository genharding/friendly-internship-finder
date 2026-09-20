# friendly_internship_finder_project

## Authors: Gentry Harding, Andrew Woodhouse, Saige Antolin, Yomna Elmousalami

<ins> Table of Contents </ins>
- [Approach](#approach)
- [Key Findings and Insights](#key-findings-and-insights)
- [Potential Next Steps](#potential-next-steps)
- [Installation](#installation)
- [Usage](#usage)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Credits and Acknowledgements](#credits-and-acknowledgements)

# Approach

# Key Findings and Insights 

# Potential Next Steps

# Installation
#### TO USE
1. `git clone https://github.com/genharding/friendly-internship-finder.git` repository and `cd ai-web-app`
2. `pip install Flask`
3. `pip install -r requirements.txt`
3. add `.env` file in top ai-web-app directory and add api-key <br>
```OPENAI_API_KEY="{your api key}"``` <br>
    (note: purchase key at <a href="https://platform.openai.com/api-keys">OpenAI Platform</a>)
4. run "python app.py" or "python3 app.py" and test in http://127.0.0.1:5000
6. To stop the program type "CTRL + C"

# Usage

# Documentation
Here is some documentation regarding Groq's API, which is what we have used in this project to help search for internships and format the results: [Groq Documentation](https://platform.openai.com/docs/guides/text-generation).

# License
If you would like to modify the code please follow the Apache License 2.0: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

# Credits and Acknowledgements
On behalf of our team, we would like to thank the VT and MLH Hacks organizers, mentors, and sponsors for their continued support and collaboration throughout this project. We had so much fun working with AI to improve the internship searching process for students. We are all excited for what is in store for future VT events. 



# For Python Version

Navigate into /backend and activate the python venv with `. .venv/bin/activate`

run `flask run --debug`

*127.0.0.1:5000* is the website mockup

*127.0.0.1:5000/search* is the Hirebase api call

# For JavaScript Version

before running, make sure to install nodejs and npm

to run, just type: npm run dev

backend for now is flask. to run just type: python app.py in the command line
