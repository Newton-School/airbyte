job_roles = ["Angular Developer", "Angular JS Developer", "Associate Software Engineer", "Backend Developer", "C# Developer",
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

import requests
import json
from bs4 import BeautifulSoup
import re
def extract_experience(experience_string):
    try:
        experience_range = experience_string.split('-')
        min_experience = ''.join(re.findall(r'\d', experience_range[0].strip()))
        max_experience = ''.join(re.findall(r'\d', experience_range[1].strip()))
        return min_experience, max_experience
    except Exception as e:
        print("Not able to extract experience")
        return "", ""

def extract_min_max_ctc(salary):
    min_ctc = 0
    max_ctc = 0
    if 'la' in salary.lower() and '-' in salary:
        try:
            ctc_range = salary.split("-")
            
            min_ctc = ''.join(re.findall(r'\d', ctc_range[0].strip()))
            max_ctc = ''.join(re.findall(r'\d', ctc_range[1].strip()))
            if len(str(min_ctc)) > 5:
                min_ctc = min_ctc / 100000
            if len(str(max_ctc)) > 5:
                max_ctc = max_ctc / 100000
        except Exception as e:
            print(e)
            pass
    return min_ctc, max_ctc

def extract_job_information(job_description_url, job_openings_obj):
    techgig_response =  requests.get(job_description_url).text
    techgig_individual_beautiful_soup = BeautifulSoup(techgig_response, 'html.parser') \
        .find('div', id="job-details-block")
    
    new_job_details = {}

    about_job_details = techgig_individual_beautiful_soup.find('article', class_="post")

    job_description_list = about_job_details.find('dl', class_="description-list")

    detail_list = job_description_list.find_all('dd')
    
    # Extract Location
    new_job_details['job_location'] = detail_list[1].text.strip()

    # Extract CTC
    ctc_range = detail_list[0].text.strip()
    print(ctc_range)
    new_job_details['min_ctc'], new_job_details['max_ctc'] = extract_min_max_ctc(ctc_range)

    # Extract Experience
    experience_range = detail_list[2].text.strip()
    min_experience, max_experience = extract_experience(experience_range)
    new_job_details['min_experience'] = min_experience
    new_job_details['max_experience'] = max_experience

    # Extract Description
    decription_details = about_job_details.find_all('div', class_="content-block-normal")[1]
    
    new_job_details['job_description_raw_text'] = decription_details.get_text()
    
    return job_openings_obj | new_job_details

total_job_count = 0
for job_role in job_roles:
    page_counter = 1
    total_jobs = 0
    
    while True:
        try:
            techgigResponse = requests.get(
                'https://www.techgig.com/job_search',
                params={
                    "txtKeyword": job_role,
                    "page": page_counter,
                }
            ).text
            techgig_job_page = BeautifulSoup(techgigResponse, 'html.parser')
            job_postings = techgig_job_page.find_all('div', class_="job-box-lg")
            if len(job_postings) == 0:
                break
            for job_posting in job_postings:
                try:
                    job_posting_url = job_posting.find('a').get('href')
                    job_header_div = job_posting.find('div', class_='job-header')
                    job_title = job_header_div.find('h3').text
                    company_name = job_header_div.find('p').text
                    skill_required = job_posting.find('dl', class_="description-list").find_all('dd')[-1].text
                    job_data = {
                        "job_title": job_title,
                        "job_role": job_role,
                        "job_description_url": job_posting_url,
                        "skills": {
                            "preferredSkills": skill_required.split(','),
                        },
                        "company": company_name,
                        "job_source": "techgig"
                    }
                    print("Job Openings", json.dumps(extract_job_information(job_posting_url, job_data), indent=4))
                except:
                    print(f"Unable to Extract Job Openings")

            total_jobs += len(job_postings)
            print(page_counter, total_jobs)
            page_counter += 1
        except:
            print(f"Unable to extract jobs for {job_role}")
    
    total_job_count += total_jobs

print(total_job_count)
