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
            "skills_raw": {
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
                            'skills_raw': jobObj['tagsAndSkills'].strip(),
                            'companyName':jobObj['companyName'].strip(),
                            'jdText': self.remove_html_tags(jobObj['jobDescription'].strip()),
                            'jobType': 'Not available',
                            'role': searchJobType,
                            'companyId': jobObj['companyId'].strip(),
                        }
                        otherData = {}
                        for placeholderObj in jobObj['placeholders']:
                            if(placeholderObj['type'] == 'experience'):
                                otherData['experience'] = placeholderObj['label'].strip()
                            
                            if(placeholderObj['type'] == 'salary'):
                                otherData['salary'] = placeholderObj['label'].strip()

                            if(placeholderObj['type'] == 'location') :
                                otherData['location'] = placeholderObj['label'].strip()
                        
                        jobData.update(otherData)

                        yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(stream=stream_name, data=jobData, emitted_at=int(datetime.now().timestamp()) * 1000),
                        )
                else:
                    logger.error(f'LeadSquare Response Threw {naukriResponse.status_code} with {naukriResponse.status_code}')

        except Exception as e:
            logger.error(f'Error while running query: {str(e)}')
