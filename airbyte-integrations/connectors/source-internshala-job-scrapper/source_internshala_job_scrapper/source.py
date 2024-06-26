#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
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
from airbyte_protocol.models import AirbyteStateMessage, AirbyteStateType, AirbyteStreamState, StreamDescriptor
from airbyte_cdk.sources import Source
from bs4 import BeautifulSoup
import requests
import json
import re


class SourceInternshalaJobScrapper(Source):
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
            # Not Implemented
            main_text_url = f"https://internshala.com/jobs_ajax/python-developer-jobs"
            url = f"{main_text_url}/page-1"
            requests.get(url).json()
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema
        return AirbyteCatalog(streams=stream_schema)
    
    def extract_experience(self, experience_string):
        try:
            experience_range = experience_string.split('-')
            min_experience = ''.join(re.findall(r'\d', experience_range[0].strip()))
            max_experience = ''.join(re.findall(r'\d', experience_range[1].strip()))
            return min_experience, max_experience
        except Exception as e:
            print("Not able to extract experience")
            return "", ""
    
    @staticmethod
    def extract_min_max_ctc(salary):
        min_ctc = 0
        max_ctc = 0
        if 'lacs' in salary.lower() and '-' in salary:
            try:
                ctc_range = salary.split("-")
                
                min_ctc = ''.join(re.findall(r'\d', ctc_range[0].strip()))
                max_ctc = ''.join(re.findall(r'\d', ctc_range[1].strip()))
                if len(str(min_ctc)) > 5:
                    min_ctc = min_ctc / 100000
                if len(str(max_ctc)) > 5:
                    max_ctc = max_ctc / 100000
            except Exception as e:
                print("Not able to extract ctc")
                pass
        return min_ctc, max_ctc
    
    def extract_job_information(self, job_description_url, job_openings_obj):
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
            new_job_details["min_ctc"], new_job_details["max_ctc"] = self.extract_min_max_ctc(ctc_range)
        except:
            print("Not Able to extract CTC")

        # Extract Experience
        try:
            experience_range = intershala_individual_beautiful_soup \
                .find('div', class_='job-experience-item') \
                .find('div', class_='desktop-text') \
                .text.strip()
            new_job_details["min_experience"], new_job_details["max_experience"] =self.extract_experience(experience_range)
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


    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        from .job_roles import job_roles

        for job_role in job_roles:
            job_role_data = {'title': job_role}
            yield AirbyteMessage(
                type=Type.RECORD,
                record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
            )
            try:
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
                        yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='companies', data=company_data, emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                        )
                        
                        profile_meta_soup = internship_meta_soup.find('h3', class_='profile')
                        job_title = profile_meta_soup.text.strip()
                        job_description_url = f"https://internshala.com{profile_meta_soup.find('a').get('href')}"
                        job_data = {
                            "job_title": job_title,
                            "job_role": job_role,
                            "job_description_url": job_description_url,
                            "job_description_url_without_job_id": job_description_url,
                            "company": company_name,
                            "job_source": "internshala"
                        }
                        yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='job_openings', data=self.extract_job_information(job_description_url, job_data), emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                        )

                    page_counter += 1
            except Exception as e:
                print(f"Skipping for {job_role} Job Role with error {e}")

        for stream_name in ["companies", "job_openings", "recruiter_details", "job_roles"]:
            yield AirbyteMessage(
                type=Type.STATE,
                state=AirbyteStateMessage(
                    type=AirbyteStateType.STREAM,
                    stream=AirbyteStreamState(
                        stream_descriptor=StreamDescriptor(
                            name=stream_name
                        )
                    ),
                )
            )