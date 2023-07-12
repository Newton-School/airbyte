#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
import requests
import re
from typing import Dict, Generator

from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)
from airbyte_cdk.sources import Source

app_id = "110"
system_id = "110"


class SourceNaukriJobScrapper(Source):
    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        """
        Tests if the input configuration can be used to successfully connect to the integration
            e.g: if a provided Stripe API token can be used to connect to the Stripe API.

        :param logger: Logging object to display debug/info/error to the logs
            (logs will not be accessible via airbyte UI if they are not passed to this logger)
        :param config: Json object containing the configuration of this source, content of this json is as specified in
        the properties of the spec.yaml file

        :return: AirbyteConnectionStatus indicating a Success or Failure
        """
        try:
            searchJobType = config['job_role']

            naukriResponse = requests.get(

                'https://www.naukri.com/jobapi/v3/search?noOfResults=30&urlType=search_by_keyword&searchType=adv&src=jobsearchDesk',
                params={
                    'keyword': searchJobType,
                    'pageNo': 1,
                    'jobAge': 1,
                },
                headers={
                    'appid': app_id,
                    'systemid': system_id,
                }
            )

            if 200 <= naukriResponse.status_code < 300:
                return AirbyteConnectionStatus(status=Status.SUCCEEDED)

            return AirbyteConnectionStatus(status=Status.FAILED,
                                           message=f"Threw {naukriResponse.status_code} Status code, with {naukriResponse.json()} response.")
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema

        return AirbyteCatalog(streams=stream_schema)

    @staticmethod
    def remove_html_tags(text):
        clean = re.compile('<.*?>')
        return re.sub(clean, ' ', text)

    @staticmethod
    def get_labels(my_list):
        labels = []
        for item in my_list:
            labels.append(item["label"])
        return labels
    
    @staticmethod
    def updated_url(original_string, string_to_remove):
        updated_string = original_string.replace(string_to_remove, "")
        return updated_string

    @staticmethod
    def get_naukri_request_response(job_type, page_number=1):
        naukri_response = requests.get(
            'https://www.naukri.com/jobapi/v3/search?noOfResults=30&urlType=search_by_keyword&searchType=adv&src=jobsearchDesk',
            params={
                'keyword': job_type,
                'pageNo': page_number,
                'jobAge': 1,
            },
            headers={
                'appid': app_id,
                'systemid': system_id,
            })
        if 200 <= naukri_response.status_code < 300:
            return naukri_response.json()
        return {}

    @staticmethod
    def extract_min_max_ctc(salary):
        min_ctc = 0
        max_ctc = 0
        if 'Lacs' in salary and '-' in salary:
            try:
                min_ctc, max_ctc = salary.split(" ")[0].split("-")
                min_ctc = min_ctc.replace(',', '')
                min_ctc = float(re.findall(r"[-+]?\d*\.\d+|\d+", min_ctc)[0])
                if len(str(min_ctc)) > 5:
                    min_ctc = min_ctc/100000
                max_ctc = float(max_ctc)
            except:
                pass
        return {
            'min_ctc': min_ctc,
            'max_ctc': max_ctc
        }

    @staticmethod
    def get_relevancy_score(min_ctc, min_experience, department, skills):
        is_relevant = True
        if min_experience not in [0, 1, 2]:
            is_relevant = False
        if min_ctc < 3:
            is_relevant = False
        if min_ctc == 0:
            is_relevant = True
        non_preferred_departments = ['sales', 'retail', 'business development', 'recruitment', 'administration', 'manufacturing',
                                     'finance', 'audit']
        for dept in non_preferred_departments:
            if dept in department.lower():
                is_relevant = False
        if is_relevant:
            return 1
        return 0

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        config_role = config['job_role']
        if config_role == 'dummy':
            job_roles = ["Angular Developer", "Angular JS Developer", "Associate Software Engineer","Backend Developer","C# Developer","C++ Developer","Developer","Client-Side Developer","Embedded Software Developer","Embedded Software Engineer","Front End Web Developer","Front-End Developer","Frontend Angular Developer","Frontend Architect","Frontend Developer","Frontend Engineer","Frontend Web Developer","Full Stack Developer","Full Stack Java Developer","Full Stack Software Engineer","HTML Developer","Java Backend Developer","Java Developer","Java Fullstack Developer","Java Microservices Developer","Java React Developer","Java SpringBoot Developer","Javascript Developer","Junior Software Developer","Junior Software Engineer","Mean Stack Developer","MERN Stack Developer","MIS","MIS Analyst","MIS Executive and Analyst","Node JS Developer","Node.js Developer","Python Developer","Python/Django Developer","React Developer","React Js Developer","React.js Developer","React/Frontend Developer","React+Node Js Developer","RIM Support Engineer","Ruby on Rails Developer","SAP HANA DB Administration Software Development Engineer","Software Developer","Software Development Engineer","Software Engineer","Software Engineer Trainee","Software Programmer","Solution Developer","SYBASE Database Administration Software Development Engineer","Trainee Associate Engineer","Trainee Software Developer","Trainee Software Engineer","UI Angular Developer","UI Developer","UI Frontend Developer","UI/Frontend Developer","UI/UX Developer","Web and Software Developer","Web Designer & Developer","Web Designer and Developer","Web Designer/Developer","Web Developer","Web Developer and Designer","Website Designer","website developer","XML and C# Developer","PHP Developer","Laravel Developer","Magento Developer","Drupal Developer","Dotnet developer",".net ","Vue.JS Developer","Python/Django Developer","GoLang developer","jQuery","Springboot Developer","Actuarial Analyst","Analyst","AR Analyst","Associate Business Analyst","Automation Test Analyst","Azure Data Engineer","Big Data Engineer","Business Analyst","Business Data Analyst","Data Analyst","Data Analytics Trainer","Data Research Analyst","Data Researcher","Data Science Engineer","Data Scientist","Database Administrator","Functional Analyst","Junior Analyst","Junior Research Analyst","KYC Analyst","Market Research Analyst","Power BI Developer","Product Analyst","Programmer Analyst","QA Analyst","Quality Analyst","Real Time Analyst","Reconciliation Analyst","Research Analyst","Risk Analyst","Sales Analyst","Salesforce Business Analyst","Service Desk Analyst","SOC Analyst","SQL Developer","Android Application Developer","Android Developer","Android Mobile Application Developer","Application Developer","Application Support Engineer","Flutter Developer","iOS Application Developer","IOS Developer","Mobile App Developer","Mobile Application Developer","Associate Technical Support Engineer","Automation Engineer","Automation Test Engineer","Batch Support Engineer","Desktop Support Engineer","Genesys Support Engineer","IT Support Engineer","Network Support Engineer","QA Automation Engineer","SaaS Support Engineer","Security Engineer","Test Automation Engineer","Systems Support Engineer","Software Development Engineer - Test","Software Test Engineer","Software Tester","Support Engineer","Tech Customer Support Engineer","Technical Support Engineer","Servicenow Developer","SharePoint Developer","Shopify Developer","Unity Game Developer","WordPress & Shopify Developer","WordPress Developer","Wordpress Web Developer","Unreal Developer"]
            for query in job_roles:
                has_more = True
                page_no = 0
                while has_more:
                    url = f"https://jobseeker-api.hirist.com/v2/jobfeed/-1/v3/search?pageNo={page_no}&query={query}&loc=&minexp=0&maxexp=2&range=0&boost=1"
                    try:
                        resp = requests.get(url).json()
                    except Exception as e:
                        print(str(e))
                        break
                    jobs = resp.get('jobs') or []
                    for job in jobs:
                        skills = {"preferredSkills": [], "otherSkills": []}
                        tags = job.get('tags') or []
                        for tag in tags:
                            skill_name = tag.get('name')
                            is_mandatory = tag.get('isMandatory')
                            if is_mandatory:
                                skills['preferredSkills'].append(skill_name)
                            else:
                                skills['otherSkills'].append(skill_name)

                        locations = job.get('locations')

                        location_name = locations[0].get('name') if locations else ""

                        company_data = job.get('companyData')
                        if company_data:
                            company_name = company_data.get('companyName')
                            company = {
                                "name": company_name
                            }

                            yield AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(
                                            stream='companies', data=company, emitted_at=int(datetime.now().timestamp()) * 1000
                                    )
                            )
                        else:
                            company_name = ""

                        job_opening = {
                            "job_role": query,
                            "job_title": job.get('jobdesignation') or "",
                            "min_experience": job.get('min') or "",
                            "max_experience": job.get('max') or "",
                            "job_description_url": job.get('jobDetailUrl') or "",
                            "skills": skills,
                            "min_ctc": job.get('minSal') or "",
                            "max_ctc": job.get('maxSal') or "",
                            "company": company_name,
                            "job_source": "hirist",
                            "job_location": location_name,
                            "raw_response": job,
                            "job_description_url_without_job_id": job.get('jobDetailUrl') or "",
                            "job_description_raw_text": job.get('introText') or ""
                        }

                        yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='job_openings', data=job_opening, emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                        )

                        recruiter = job.get('recruiter')
                        if recruiter:
                            recruiter_details = {
                                "hiring_manager_for_job_link": job.get('jobDetailUrl'),
                                "name": recruiter.get('recruiterName'),
                                "company": company_name,
                                "short_intro": recruiter.get('designation'),
                                "linkedin_profile_url": f"dummy_{company_name}"
                            }
                            yield AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(
                                            stream='recruiter_details', data=recruiter_details,
                                            emitted_at=int(datetime.now().timestamp()) * 1000
                                    ),
                            )

                    has_more = resp.get('hasMore')
                    page_no += 1
        else:
            job_roles = [config_role]

        for job_role in job_roles:
            job_role_data = {'title': job_role}
            yield AirbyteMessage(
                type=Type.RECORD,
                record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
            )

            response_for_pages = self.get_naukri_request_response(job_role)
            if 'noOfJobs' in response_for_pages:
                total_pages = response_for_pages['noOfJobs'] // 30
            else:
                total_pages = 1

            for page in range(1, total_pages):
                response_for_job = self.get_naukri_request_response(job_role, page)

                for job_resp in response_for_job['jobDetails']:
                    company_data = {"name": job_resp['companyName'].strip()}
                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream='companies', data=company_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                    )

                    jd_url = "https://www.naukri.com" + job_resp.get('jdURL', '')
                    job_data = {
                        'job_title': job_resp['title'].strip(),
                        'job_role': job_role_data['title'],
                        'job_description_url': jd_url,
                        'company': company_data['name'],
                        'job_description_url_without_job_id': jd_url.replace(job_resp.get('jobId', ''), ''),
                        'job_description_raw_text': self.remove_html_tags(job_resp['jobDescription'].strip()),
                        'job_source': 'naukri'
                    }

                    job_extended_response = requests.get(
                        'https://www.naukri.com/jobapi/v4/job/' + job_resp.get('jobId', ''),
                        headers={
                            'appid': app_id,
                            'systemid': system_id,
                        })
                    extended_job_details = job_extended_response.json()['jobDetails']

                    salary = self.extract_min_max_ctc(extended_job_details['salaryDetail']['label'])
                    min_ctc = salary['min_ctc']
                    max_ctc = salary['max_ctc']
                    job_extended_data = {
                        'skills': {
                            'preferredSkills': self.get_labels(extended_job_details['keySkills']['preferred']),
                            'otherSkills': self.get_labels(extended_job_details['keySkills']['other']),
                        },
                        'department': extended_job_details['functionalArea'],
                        'job_type': extended_job_details['employmentType'],
                        'min_ctc': min_ctc,
                        'max_ctc': max_ctc,
                        'relevancy_score': self.get_relevancy_score(
                            min_ctc, extended_job_details['minimumExperience'], extended_job_details['functionalArea'],
                            self.get_labels(extended_job_details['keySkills']['preferred'])
                        ),
                        'raw_response': extended_job_details,
                        'min_experience': extended_job_details['minimumExperience'],
                        'max_experience': extended_job_details['maximumExperience']
                    }

                    for placeholder in job_resp['placeholders']:
                        if placeholder['type'] == 'location':
                            job_extended_data['job_location'] = placeholder['label'].strip()
                    hr_name = extended_job_details.get('vcard', {}).get('name', '')
                    final_data = job_data | job_extended_data

                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream='job_openings', data=final_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                    )

                    if hr_name:
                        recruiter_details = {
                            'name': hr_name,
                            'hiring_manager_for_job_link': jd_url,
                            'company': job_resp['companyName'].strip(),
                            'linkedin_profile_url': f"dummy_{hr_name}_{job_resp['companyName'].strip()}"
                        }

                        yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(stream='recruiter_details', data=recruiter_details, emitted_at=int(datetime.now().timestamp()) * 1000),
                        )
