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
from airbyte_cdk.sources import Source
from bs4 import BeautifulSoup
import requests
import json


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

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema
        return AirbyteCatalog(streams=stream_schema)
    
    def extract_job_information(job_description_url, job_openings_obj):
        intershala_response =  requests.get(job_description_url).text
        intershala_individual_beautiful_soup = BeautifulSoup(intershala_response, 'html.parser') \
            .find('div', class_="detail_view")
        
        # Extract location
        job_location = intershala_individual_beautiful_soup.find('p', id='location_names').text.strip()
        
        # Extract CTC
        ctc_range = intershala_individual_beautiful_soup \
            .find('div', class_='salary_container') \
            .find('div', class_='salary') \
            .find('span', class_='desktop') \
            .text.strip()
        ctc_range_split = ctc_range.split('-')
        min_ctc = ctc_range_split[0].strip()
        max_ctc = ctc_range_split[1].strip()

        # Extract Experience
        experience_range = intershala_individual_beautiful_soup \
            .find('div', class_='job-experience-item') \
            .find('div', class_='desktop-text') \
            .text.strip()
        experience_range_split = experience_range.split('-')
        min_experience = experience_range_split[0].strip()
        max_experience = experience_range_split[1].strip()

        # Extract Description
        description_text = intershala_individual_beautiful_soup.find('div', 'about_company_text_container').text.strip()

        # Extract Skills
        skills_heading_div = intershala_individual_beautiful_soup.find('div', 'skills_heading')

        skill_child_div = skills_heading_div.find_next_sibling('div')

        skill_required = []
        for skill in skill_child_div.find_all('span'):
            skill_required.append(skill.text)
        
        new_job_details = {
            "min_ctc": min_ctc,
            "max_ctc": max_ctc,
            "min_experience": min_experience,
            "max_experience": max_experience,
            "skills": {
                "preferredSkills": skill_required
            },
            "job_description_raw_text": description_text,
            "job_location": job_location
        }

        return job_openings_obj | new_job_details

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        try:
            from .job_roles import job_roles

            for job_role in job_roles:
                job_role_data = {'title': job_role}
                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                )

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
        except:
            print(f"Skipping for {job_role} Job Role")
