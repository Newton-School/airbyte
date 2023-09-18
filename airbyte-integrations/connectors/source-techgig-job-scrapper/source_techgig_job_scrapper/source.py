#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
from typing import Dict, Generator
import requests
from bs4 import BeautifulSoup

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


class SourceTechgigJobScrapper(Source):
    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        try:
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema
        return AirbyteCatalog(streams=stream_schema)
    
    def extract_job_information(self, job_description_url, job_openings_obj):
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
        try:
            ctc_range = detail_list[0].text.strip()
            min_ctc = ctc_range.split('-')[0]
            max_ctc = ctc_range.split('-')[1]
            new_job_details['min_ctc'] = min_ctc.strip()
            new_job_details['max_ctc'] = max_ctc.strip()
        except:
            new_job_details['min_ctc'] = detail_list[0].text.strip()
            print("Unable to Extract CTC")


        # Extract Experience
        try:
            experience_range = detail_list[2].text.strip()
            min_experience = experience_range.split('-')[0].strip()
            max_experience = experience_range.split('-')[1].strip()
            new_job_details['min_experience'] = min_experience
            new_job_details['max_experience'] = max_experience
        except:
            new_job_details['min_experience'] = detail_list[2].text.strip()
            print("Unable to Extract CTC")

        # Extract Description
        decription_details = about_job_details.find_all('div', class_="content-block-normal")[1]
        print(decription_details)
        
        new_job_details['job_description_raw_text'] = decription_details.get_text()
        
        return job_openings_obj | new_job_details


    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        from .job_roles import job_roles
        job_role_data = {'title': job_role}
        yield AirbyteMessage(
            type=Type.RECORD,
            record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
        )

        for job_role in job_roles:
            page_counter = 1
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
                            company_data = {"name": company_name}
                            yield AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(
                                            stream='companies', data=company_data, emitted_at=int(datetime.now().timestamp()) * 1000
                                    ),
                            )
                            skill_required = job_posting.find('dl', class_="description-list").find_all('dd')[-1].text
                            job_data = {
                                "job_title": job_title,
                                "job_role": job_role,
                                "job_description_url": job_posting_url,
                                "skills": {
                                    "preferredSkills": skill_required,
                                },
                                "company": company_name,
                                "job_source": "techgig"
                            }
                            yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='job_openings', data=self.extract_job_information(job_posting_url, job_data), emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                            )
                        except:
                            print(f"Unable to Extract Job Openings")
                    page_counter += 1
                except:
                    print(f"Unable to extract jobs for {job_role}")