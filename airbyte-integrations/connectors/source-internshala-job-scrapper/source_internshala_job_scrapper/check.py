job_roles = ["Angular JS Developer", "Associate Software Engineer", "Backend Developer", "C# Developer",
"C++ Developer", "Developer", "Client-Side Developer", "Embedded Software Developer", "Embedded Software Engineer",
"Front End Web Developer", "Front-End Developer", "Frontend Angular Developer", "Frontend Architect",
"Frontend Developer", "Frontend Engineer", "Frontend Web Developer", "Full Stack Developer",
"Full Stack Java Developer", "Full Stack Software Engineer", "HTML Developer", "Java Backend Developer",
"Java Developer", "Java Fullstack Developer", "Java Microservices Developer", "Java React Developer",
"Java SpringBoot Developer", "Javascript Developer", "Junior Software Developer", "Junior Software Engineer",
"Mean Stack Developer", "MERN Stack Developer", "MIS", "MIS Analyst", "MIS Executive and Analyst",
"Node JS Developer", "Node.js Developer", "Python Developer", "Python/Django Developer", "React Developer",
"React Js Developer", "React.js Developer", "React/Frontend Developer", "React+Node Js Developer",
"RIM Support Engineer", "Ruby on Rails Developer", "SAP HANA DB Administration Software Development Engineer",
"Software Developer", "Software Development Engineer", "Software Engineer", "Software Engineer Trainee",
"Software Programmer", "Solution Developer", "SYBASE Database Administration Software Development Engineer",
"Trainee Associate Engineer", "Trainee Software Developer", "Trainee Software Engineer", "UI Angular Developer",
"UI Developer", "UI Frontend Developer", "UI/Frontend Developer", "UI/UX Developer", "Web and Software Developer",
"Web Designer & Developer", "Web Designer and Developer", "Web Designer/Developer", "Web Developer",
"Web Developer and Designer", "Website Designer", "website developer", "XML and C# Developer", "PHP Developer",
"Laravel Developer", "Magento Developer", "Drupal Developer", "Dotnet developer", ".net ", "Vue.JS Developer",
"Python/Django Developer", "GoLang developer", "jQuery", "Springboot Developer", "Actuarial Analyst", "Analyst",
"AR Analyst", "Associate Business Analyst", "Automation Test Analyst", "Azure Data Engineer", "Big Data Engineer",
"Business Analyst", "Business Data Analyst", "Data Analyst", "Data Analytics Trainer", "Data Research Analyst",
"Data Researcher", "Data Science Engineer", "Data Scientist", "Database Administrator", "Functional Analyst",
"Junior Analyst", "Junior Research Analyst", "KYC Analyst", "Market Research Analyst", "Power BI Developer",
"Product Analyst", "Programmer Analyst", "QA Analyst", "Quality Analyst", "Real Time Analyst",
"Reconciliation Analyst", "Research Analyst", "Risk Analyst", "Sales Analyst", "Salesforce Business Analyst",
"Service Desk Analyst", "SOC Analyst", "SQL Developer", "Android Application Developer", "Android Developer",
"Android Mobile Application Developer", "Application Developer", "Application Support Engineer",
"Flutter Developer", "iOS Application Developer", "IOS Developer", "Mobile App Developer",
"Mobile Application Developer", "Associate Technical Support Engineer", "Automation Engineer",
"Automation Test Engineer", "Batch Support Engineer", "Desktop Support Engineer", "Genesys Support Engineer",
"IT Support Engineer", "Network Support Engineer", "QA Automation Engineer", "SaaS Support Engineer",
"Security Engineer", "Test Automation Engineer", "Systems Support Engineer",
"Software Development Engineer - Test", "Software Test Engineer", "Software Tester", "Support Engineer",
"Tech Customer Support Engineer", "Technical Support Engineer", "Servicenow Developer", "SharePoint Developer",
"Shopify Developer", "Unity Game Developer", "WordPress & Shopify Developer", "WordPress Developer",
"Wordpress Web Developer", "Unreal Developer"]

from bs4 import BeautifulSoup
import requests
import json

def extract_job_information(job_description_url, job_openings_obj):
    intershala_response =  requests.get(job_description_url).text
    intershala_individual_beautiful_soup = BeautifulSoup(intershala_response, 'html.parser') \
        .find('div', class_="detail_view")
    
    new_job_details = {}
    
    # Extract location
    try:
        new_job_details["job_location"] = intershala_individual_beautiful_soup.find('p', id='location_names').text.strip()
    except:
        print("Not Able to Extract Locations")
    
    # Extract CTC
    try:
        ctc_range = intershala_individual_beautiful_soup \
            .find('div', class_='salary_container') \
            .find('div', class_='salary') \
            .find('span', class_='desktop') \
            .text.strip()
        ctc_range_split = ctc_range.split('-')
        new_job_details["min_ctc"] = ctc_range_split[0].strip()
        new_job_details["max_ctc"] = ctc_range_split[1].strip()
    except:
        print("Not Able to extract CTC")

    # Extract Experience
    try:
        experience_range = intershala_individual_beautiful_soup \
            .find('div', class_='job-experience-item') \
            .find('div', class_='desktop-text') \
            .text.strip()
        experience_range_split = experience_range.split('-')
        new_job_details["min_experience"] = experience_range_split[0].strip()
        new_job_details["max_experience"] = experience_range_split[1].strip()
    except:
        print("Not Able to Extract Experience")

    # Extract Description
    try:
        new_job_details["job_description_raw_text"] = intershala_individual_beautiful_soup.find('div', 'about_company_text_container').text.strip()
    except:
        print("Not Able to Extract Description")

    # Extract Skills
    try:
        skills_heading_div = intershala_individual_beautiful_soup.find('div', 'skills_heading')

        skill_child_div = skills_heading_div.find_next_sibling('div')

        skill_required = []
        for skill in skill_child_div.find_all('span'):
            skill_required.append(skill.text)
        new_job_details["skills"] = {
            "preferredSkills": skill_required
        }
    except:
        print("Not Able to Extract Skills")

    return job_openings_obj | new_job_details

for job_role in job_roles:
    job_title_jobs_text = f"{'-'.join(job_role.lower().split())}-jobs"
    search_parameter_url = f"https://internshala.com/job/get_search_criterias/{job_title_jobs_text}"
    search_parameter_response = requests.get(search_parameter_url).json()
    if int(search_parameter_response['location_count']) >= 630:
        continue

    main_text_url = f"https://internshala.com/jobs_ajax/{job_title_jobs_text}"
    page_counter = 1
    while True:
        url = f"{main_text_url}/page-{page_counter}"
        intershala_response =  requests.get(url).json()
        intershala_list_html = intershala_response["internship_list_html"]
        if int(intershala_response['currentPageCount']) == 0:
            break

        intershala_beautiful_soup = BeautifulSoup(intershala_list_html, 'html.parser')

        individual_jobs = intershala_beautiful_soup.find_all('div', class_ = "individual_internship")
        for div_soup in individual_jobs:
            classnames = div_soup.get('class', [])
            if 'no_result_message' in classnames:
                break

            internship_meta_soup = div_soup.find('div', class_='internship_meta')

            company_name = internship_meta_soup.find('h4', class_='company_name').text.strip()
            company_data = {"name": company_name}
            
            profile_meta_soup = internship_meta_soup.find('h3', class_='profile')
            job_title = profile_meta_soup.text.strip()
            job_description_url = f"https://internshala.com{profile_meta_soup.find('a').get('href')}"
            job_data = {
                "job_title": job_title,
                "job_role": job_role,
                "job_description_url": job_description_url,
                "company": company_name,
                "job_source": "internshala"
            }
            print('job_openings', json.dumps(extract_job_information(job_description_url, job_data), indent=4))

        page_counter += 1
