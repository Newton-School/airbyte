#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
from typing import Dict, Generator
import requests
import re

from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteRecordMessage,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)
from airbyte_cdk.sources import Source


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
                        'pageNo' : 1,
                        'jobAge': 1,
                    },
                headers={
                    'appid': app_id,
                    'systemid': system_id,
                }
            )
  
            if 200 <= naukriResponse.status_code < 300:
                return AirbyteConnectionStatus(status=Status.SUCCEEDED)

            return AirbyteConnectionStatus(status=Status.FAILED, message=f"Threw {naukriResponse.status_code} Status code, with {naukriResponse.json()} response.")
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        """
        Returns an AirbyteCatalog representing the available streams and fields in this integration.
        For example, given valid credentials to a Postgres database,
        returns an Airbyte catalog where each postgres table is a stream, and each table column is a field.

        :param logger: Logging object to display debug/info/error to the logs
            (logs will not be accessible via airbyte UI if they are not passed to this logger)
        :param config: Json object containing the configuration of this source, content of this json is as specified in
        the properties of the spec.yaml file

        :return: AirbyteCatalog is an object describing a list of all available streams in this source.
            A stream is an AirbyteStream object that includes:
            - its stream name (or table name in the case of Postgres)
            - json_schema providing the specifications of expected schema for this stream (a list of columns described
            by their names and types)
        """

        fields = {
            "jobType": {
                "type": "string"
            },
            "title": {
                "type": "string"
            },
            "role": {
                "type": "string"
            },
            "jobId": {
                "type": "number"
            },
            "jdUrl": {
                "type": "string"
            },
            "jdText": {
                "type": "string"
            },
            "experience": {
                "type": "string"
            },
            "companyName": {
                "type": "string"
            },
            "location": {
                "type": "string"
            },
            "salary": {
                "type": "string"
            },
            "skills": {
                "type": "object"
            },
            "department": {
                "type": "string"
            },
            "employmentType": {
                "type": "string"
            },
            "relevancy": {
                "type": "boolean"
            },
            "extraDetails": {
                "type": "string"
            },
            "companyId": {
                "type": "string"
            },

        }

        stream_name = "NaukriJobs"
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": fields,
        }

        streams = [
            {
                "name": stream_name,
                "supported_sync_modes": [
                    "full_refresh"
                ],
                "source_defined_cursor": False,
                "json_schema": json_schema
            }
        ]

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
    def updated_url(original_string,string_to_remove):
        updated_string = original_string.replace(string_to_remove, "")
        return updated_string

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        """
        Returns a generator of the AirbyteMessages generated by reading the source with the given configuration,
        catalog, and state.

        :param logger: Logging object to display debug/info/error to the logs
            (logs will not be accessible via airbyte UI if they are not passed to this logger)
        :param config: Json object containing the configuration of this source, content of this json is as specified in
            the properties of the spec.yaml file
        :param catalog: The input catalog is a ConfiguredAirbyteCatalog which is almost the same as AirbyteCatalog
            returned by discover(), but
        in addition, it's been configured in the UI! For each particular stream and field, there may have been provided
        with extra modifications such as: filtering streams and/or columns out, renaming some entities, etc
        :param state: When a Airbyte reads data from a source, it might need to keep a checkpoint cursor to resume
            replication in the future from that saved checkpoint.
            This is the object that is provided with state from previous runs and avoid replicating the entire set of
            data everytime.

        :return: A generator that produces a stream of AirbyteRecordMessage contained in AirbyteMessage object.
        """

        stream_name = "NaukriJobs"
        try:
            app_id = config['appid']
            system_id = config['systemid']
            searchJobType = config['jobtype']

            for pageNo in range(1,50):
                naukriResponse = requests.get(
                    'https://www.naukri.com/jobapi/v3/search?noOfResults=30&urlType=search_by_keyword&searchType=adv&src=jobsearchDesk', 
                    params={
                        'keyword': searchJobType,
                        'pageNo' : pageNo,
                        'jobAge': 1,
                    },
                    headers={
                        'appid': app_id,
                        'systemid': system_id,
                    })
                if 200 <= naukriResponse.status_code < 300:
                    for jobObj in naukriResponse.json()['jobDetails']:
                        jobData = {
                            'jobId': jobObj['jobId'].strip(),
                            'title': jobObj['title'].strip(),
                            'jdUrl': "https://www.naukri.com"+jobObj['jdURL'].strip(),
                            'companyName':jobObj['companyName'].strip(),
                            'jdText': self.remove_html_tags(jobObj['jobDescription'].strip()),
                            'jobType': 'Not available',
                            'role': searchJobType,
                            'companyId': jobObj['companyId'].strip(),
                        }

                        internal_response = requests.get(
                            'https://www.naukri.com/jobapi/v4/job/'+jobObj['jobId'],
                            headers={
                                'appid': app_id,
                                'systemid': system_id,
                            })
                        internalObj = internal_response.json()['jobDetails'] 

                        internalData = {
                            'skills': {
                                'preferredSkills': self.get_labels(internalObj['keySkills']['preferred']),
                                'otherSkills' : self.get_labels(internalObj['keySkills']['other']),  
                            },
                            'department': internalObj['functionalArea'],
                            'employmentType': internalObj['employmentType'],
                            'relevancy' : True if internalObj['maximumExperience'] <= 1 or internalObj['minimumExperience'] <= 1 else False,
                            'salary' : internalObj['salaryDetail']['label'],
                            'extraDetails': internalObj,
                            'minimumExperience': internalObj['minimumExperience'],
                            'maximumExperience': internalObj['maximumExperience'],
                            'withoutJobId' : self.updated_url(f"https://www.naukri.com{jobObj['jdURL']}", f"-{jobObj['jobId']}")
                        }

                        for placeholderObj in jobObj['placeholders']:
                            if(placeholderObj['type'] == 'location') :
                                internalData['location'] = placeholderObj['label'].strip()
                        
                        jobData.update(internalData)

                        yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(stream=stream_name, data=jobData, emitted_at=int(datetime.now().timestamp()) * 1000),
                        )
                else:
                    logger.error(f'LeadSquare Response Threw {naukriResponse.status_code} with {naukriResponse.status_code}')

        except Exception as e:
            logger.error(f'Error while running query: {str(e)}')
