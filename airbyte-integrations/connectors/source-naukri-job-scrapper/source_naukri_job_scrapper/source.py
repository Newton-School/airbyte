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

app_id = 110
system_id = 110

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
            app_id = config['appid']
            system_id = config['systemid']
            searchJobType = config['jobtype']

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

        with open('streams_schema.json', 'r') as f:
            streams = json.load(f)

        return AirbyteCatalog(streams=streams)

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

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        job_type = config['jobtype']

        job_role_data = {'title': job_type}
        yield AirbyteMessage(
            type=Type.RECORD,
            record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
        )

        response_for_pages = self.get_naukri_request_response(job_type)
        if 'noOfJobs' in response_for_pages:
            total_pages = response_for_pages['noOfJobs'] // 30
        else:
            total_pages = 1

        for page in range(1, total_pages):
            response_for_job = self.get_naukri_request_response(job_type, page)

            for job_resp in response_for_job.json()['jobDetails']:
                company_data = {"name": job_resp['companyName'].strip()}
                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
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
                    'https://www.naukri.com/jobapi/v4/job/' + job_data['jobId'],
                    headers={
                        'appid': app_id,
                        'systemid': system_id,
                    })
                extended_job_details = job_extended_response.json()['jobDetails']

                job_extended_data = {
                    'skills': {
                        'preferredSkills': self.get_labels(extended_job_details['keySkills']['preferred']),
                        'otherSkills': self.get_labels(extended_job_details['keySkills']['other']),
                    },
                    'department': extended_job_details['functionalArea'],
                    'job_type': extended_job_details['employmentType'],
                    'relevancy': True if extended_job_details['minimumExperience'] in [0, 1] else False,
                    'salary': extended_job_details['salaryDetail']['label'],
                    'raw_response': extended_job_details,
                    'min_experience': extended_job_details['minimumExperience'],
                    'max_experience': extended_job_details['maximumExperience']
                }

                for placeholder in job_resp['placeholders']:
                    if placeholder['type'] == 'location':
                        job_extended_data['job_location'] = placeholder['label'].strip()

                final_data = job_data | job_extended_data

                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(stream='job_openings', data=final_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                )
