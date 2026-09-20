# friendly_internship_finder_project

## Authors: Gentry Harding, Andrew Woodhouse, Saige Antolin, Yomna Elmousalami

<ins> Table of Contents </ins>
- [Approach](#approach)
- [Key Findings and Insights](#key-findings-and-insights)
- [Potential Next Steps](#potential-next-steps)
- [Installation](#installation)
- [Documentation](#documentation)
- [License](#license)
- [Credits and Acknowledgements](#credits-and-acknowledgements)


## Official Link to our final product: https://friendlyinternshipfinder.com/


# Approach
The goal of our product is to make an application that lets students apply to internships much more easily. There are not many job boards specifically for internships that are easily accessible to students. Often times, students have to rely on job boards with outdated and ghost jobs. To minimize some of the headache that students go through, we decided to create this application to allow students to quickly find the top internships that matches their skillsets without having to go through so many filters or unorganized job boards. This way everyone can have an easier time applying to jobs and preparing for interviews. 

# Key Findings and Insights 
When you first navigate the website, it brings you to the main page where you will type all of your basic information. You have the options of adding your major, selecting the specific classes for your major, and/or adding specific keywords to narrow your search further. After you click the "Find Internships..." button, you will be directed to a new page with the top 3 internships that best matches what the user inputs and when you click the "Apply" button, it directs you to the job posting. From this project, we learned how to create ai agents and web scraping techniques such as Selenium and Beautiful Soup to scrape data from the Virginia Tech Website. Furthermore, we learned how to deploy our application to an official website. Lastly, we learned how to communicate our knowledge to each other, which helped us fill in the gaps in our knowledge. 

# Potential Next Steps

- Adding different countries so people from diffent countries and provinces to specify search results more efficiently. 

- Use a different model that is faster but takes up less space. Using databricks to clean data, and store our product more efficiently. 

- Add more majors instead of just one as well adding and deleting certain classes rather than just purley a checklist. 

- Add more internship listings, but that would require using a better subscription service for groq, or running our own models. 

- Add a resume and have the application autoapply to jobs as well.

# Installation
#### TO USE
1. `git clone https://github.com/genharding/friendly-internship-finder.git` repository and `cd ai-web-app`
2. `pip install -r requirements.txt`
3. add `.env` file in the main directory (Use a hirebase api key, groq api key)

Heres how to run the application, depending on the language:

### To run it:

activate the python venv with `. .venv/bin/activate`

run `flask run --debug`

*127.0.0.1:5000* is the website mockup

*127.0.0.1:5000/search* is the Hirebase api call



OR, just directly access this url: https://friendlyinternshipfinder.com/


# Documentation
Here is some documentation regarding Groq's API, which is what we have used in this project to help search for internships and format the results: [Groq Documentation](https://platform.openai.com/docs/guides/text-generation). We also used hirebase api to help find internships a lot faster than manually [Hirebase Documentation](https://www.hirebase.org/docs/api-reference/jobs/search-post)

# License
If you would like to modify the code please follow the Apache License 2.0: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

# Credits and Acknowledgements
On behalf of our team, we would like to thank the VT and MLH Hacks organizers, mentors, and sponsors for their continued support and collaboration throughout this project. We had so much fun working with AI to improve the internship searching process for students. We are all excited for what is in store for future VT events. 



