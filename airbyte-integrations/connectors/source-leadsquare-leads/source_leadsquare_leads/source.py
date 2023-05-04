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
import requests


class SourceLeadsquareLeads(Source):

    required_fields = [
        "ProspectId", 
        "Bucket", 
        "City", 
        "CollegeCity", 
        "CollegeName",
        "CreatedBy",
        "CreatedOn",
        "CurrentInterestedCourse",
        "DateOfBirth",
        "Email",
        "FirstName",
        "GraduationYear",
        "HighestQualification",
        "LastActivity",
        "LastActivityDate",
        "LastCallConnectionStatus",
        "LastCallStatus",
        "LastCallSubStatus",
        "LastName",
        "LeadAge",
        "LeadName",
        "LeadNumber",
        "LeadOrigin",
        "LeadOwner",
        "LeadQuality",
        "LeadScore",
        "LeadStage",
        "LeadStatus",
        "LeadSubStatus",
        "MidFunnelBuckets",
        "MidFunnelCount",
        "ModifiedOn",
        "NetworkId",
        "Owner",
        "PriorityStatus",
        "ProductGraduationWar"
        "ProspectId",
        "ReactivationBucket",
        "ReactivationDate",
        "SourceIntendedCourse",
        "SquadstackCalling",
        "SquadstackQualificationStatus",
        "UTMCampaign",
        "UTMMedium",
        "UTMReferer",
        "UTMSource",
        "WorkExperience",
        "YearOfPassingInText", 
    ]

    def get_stream_fields(self):
        stream_fields = {}
        for field_name in self.required_fields:
            stream_fields[field_name] = {
                "type": "string"
            }
        return stream_fields

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
            request_host = config['leadsquare-host']
            access_key = config['leadsquare-access-key']
            secret_key = config['leadsquare-secret-key']

            current_datetime = datetime.now()

            current_start_hour_timestamp = current_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            current_end_hour_timestamp = current_datetime.replace(hour=23, minute=59, second=59, microsecond=999)

            leadsquare_response = requests.post(
                url=f'{request_host}/v2/LeadManagement.svc/Leads.RecentlyModified?',
                params={
                    "accessKey": access_key,
                    "secretKey": secret_key,
                },
                json={
                    "Parameter": {
                        "FromDate": current_start_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        "ToDate": current_end_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    },
                    "Paging": {
                        "PageIndex": 1,
                        "PageSize": 1
                    },
                    "Sorting": {
                        "ColumnName": "CreatedOn",
                        "Direction": 1
                    }
                }
            )

            if 200 <= leadsquare_response.status_code < 300:
                return AirbyteConnectionStatus(status=Status.SUCCEEDED)

            return AirbyteConnectionStatus(status=Status.FAILED, message=f"Threw {leadsquare_response.status_code} Status code, with {leadsquare_response.json()} response.")
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

        stream_name = "LeadSquareLead"
        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": self.get_stream_fields(),
        }

        streams = [
            {
                "name": stream_name,
                "supported_sync_modes": [
                    "full_refresh",
                    "incremental",
                ],
                "source_defined_cursor": False,
                "json_schema": json_schema
            }
        ]

        return AirbyteCatalog(streams=streams)

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
        stream_name = "LeadSquareLeads"
        request_host = config['leadsquare-host']
        access_key = config['leadsquare-access-key']
        secret_key = config['leadsquare-secret-key']

        current_datetime = datetime.now()

        current_start_hour_timestamp = current_datetime.replace(minute=0, second=0, microsecond=0)
        current_end_hour_timestamp = current_datetime.replace(minute=59, second=59, microsecond=999)

        try:
            leadsquare_response = requests.post(
                url=f'{request_host}/v2/LeadManagement.svc/Leads.RecentlyModified',
                params={
                    "accessKey": access_key,
                    "secretKey": secret_key,
                },
                json={
                    "Parameter": {
                        "FromDate": current_start_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        "ToDate": current_end_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    },
                    "Columns": {
                        "Include_CSV": ','.join(self.get_stream_fields)
                    },
                    "Sorting": {
                        "ColumnName": "CreatedOn",
                        "Direction": 1
                    }
                }
            )

            if 200 <= leadsquare_response.status_code < 300:
                for leadsquare_leads in leadsquare_response.json()['Leads']:
                    lead_data = {}

                    for lead_property in leadsquare_leads["LeadPropertyList"]:
                        if lead_property["Attribute"] in self.get_stream_fields:
                            lead_data[lead_property["Attribute"]] = lead_property["Value"]

                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream=stream_name, data=lead_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                    )
            else:
                logger.error(f'LeadSquare Response Threw {leadsquare_response.status_code} with {leadsquare_response.status_code}')
        except Exception as e:
            logger.error(f'Error while running activity query: {str(e)}')
