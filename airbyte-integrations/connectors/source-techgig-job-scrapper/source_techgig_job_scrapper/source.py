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
from airbyte_protocol.models import AirbyteStateMessage, AirbyteStateType, AirbyteStreamState, StreamDescriptor
from airbyte_cdk.sources import Source
import re


class SourceTechgigJobScrapper(Source):
    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        try:
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
                print(e)
                pass
        return min_ctc, max_ctc
    
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
        ctc_range = detail_list[0].text.strip()
        new_job_details['min_ctc'], new_job_details['max_ctc'] = self.extract_min_max_ctc(ctc_range)

        # Extract Experience
        experience_range = detail_list[2].text.strip()
        min_experience, max_experience = self.extract_experience(experience_range)
        new_job_details['min_experience'] = min_experience
        new_job_details['max_experience'] = max_experience

        # Extract Description
        decription_details = about_job_details.find_all('div', class_="content-block-normal")[1]
        
        new_job_details['job_description_raw_text'] = decription_details.get_text()
        
        return job_openings_obj | new_job_details


    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        max_page = max(config['max_page'], 40)
        from .job_roles import job_roles

        for job_role in job_roles:
            page_counter = 1
            while True:
                if page_counter >= max_page:
                    break
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
                            job_title = job_header_div.find('h3').text.strip()
                            company_name = job_header_div.find('p').text.strip()
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
                                "job_description_url_without_job_id": job_posting_url,
                                "skills": {
                                    "preferredSkills": skill_required.split(','),
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
                        except Exception as e:
                            print(f"Unable to Extract Job Openings as {e}")
                    page_counter += 1
                except:
                    print(f"Unable to extract jobs for {job_role}")
    
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
    