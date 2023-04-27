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


class SourceJobScrapper(Source):
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
    def updated_url(original_string,string_to_remove):
        updated_string = original_string.replace(string_to_remove, "")
        return updated_string

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:


