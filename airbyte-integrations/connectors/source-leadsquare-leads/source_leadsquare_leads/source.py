#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Generator
import time

from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    AirbyteRecordMessage,
    AirbyteStateMessage,
    AirbyteStream,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)
from airbyte_protocol.models import AirbyteStateType, AirbyteStreamState, StreamDescriptor
from airbyte_cdk.sources import Source
import requests


class SourceLeadsquareLeads(Source):

    required_fields = [
        "ProspectID",
        "mx_Bucket", 
        "mx_City", 
        "mx_College_City", 
        "mx_College_Name",
        "CreatedBy",
        "CreatedOn",
        "mx_Current_Interested_Course",
        "mx_Date_Of_Birth",
        "EmailAddress",
        "FirstName",
        "mx_Graduation_Year",
        "mx_Highest_Qualification",
        "mx_Last_Call_Connection_Status",
        "mx_Last_Call_Status",
        "mx_Last_Call_Sub_Status",
        "LastName",
        "LeadAge",
        "LeadNumber",
        "Origin",
        "mx_Lead_Owner",
        "QualityScore01",
        "Score",
        "ProspectStage",
        "mx_status",
        "mx_Substatus",
        "mx_Mid_Funnel_Buckets",
        "mx_Mid_Funnel_Count",
        "ModifiedOn",
        "mx_Network_Id",
        "OwnerIdName",
        "mx_Priority_Status",
        "mx_Product_Graduation_Year",
        "mx_Reactivation_Bucket",
        "mx_Reactivation_Date",
        "mx_Source_Intended_Course",
        "mx_Squadstack_Calling",
        "mx_Squadstack_Qualification_Status",
        "mx_UTM_Campaign",
        "mx_UTM_Medium",
        "mx_UTM_Referer",
        "mx_UTM_Source",
        "mx_Work_Experience",
        "mx_Year_of_Passing_in_Text",
        "mx_RFD_Date",
        "mx_doc_collected",
        "mx_doc_approved",
        "mx_total_fees",
        "mx_total_revenue",
        "mx_cibil_check",
        "mx_ICP",
        "mx_Identifer",
        "mx_Organic_Inbound",
        "mx_Entrance_exam_Marks",
        "mx_Lead_Quality_Grade",
        "mx_Lead_Inherent_Intent",
        "mx_Test_Date_n_Time",
        "mx_Lead_Type",
        "Source"
    ]

    def get_stream_fields(self):
        stream_fields = {}
        for field_name in self.required_fields:
            if field_name == 'ProspectID':
                stream_fields['ProspectId'] = {
                    "type": "string",
                    }
            else:
                stream_fields[field_name] = {
                    "type": ["string", "null"],
                    }
        return stream_fields

    def get_lead_property_from_leadsquare_lead(self, attribute, leadsquare_lead):
        for lead_property in leadsquare_lead['LeadPropertyList']:
            if lead_property['Attribute'] == attribute:
                return lead_property['Value']
        return ''

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
        current_datetime = datetime.now(timezone.utc)
        current_start_hour_timestamp = current_datetime.replace(minute=0, second=0, microsecond=0)
        try:
            request_host = config['leadsquare-host']
            access_key = config['leadsquare-access-key']
            secret_key = config['leadsquare-secret-key']

            leadsquare_response = requests.post(
                url=f'{request_host}/v2/LeadManagement.svc/Leads.RecentlyModified',
                params={
                    "accessKey": access_key,
                    "secretKey": secret_key,
                },
                json={
                    "Parameter": {
                        "FromDate": (current_start_hour_timestamp - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                        "ToDate": current_start_hour_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    },
                    "Columns": {
                        "Include_CSV": ','.join(self.required_fields),
                    },
                    "Paging": {
                        "PageIndex": 1,
                        "PageSize": 5000
                    },
                    "Sorting": {
                        "ColumnName": "ModifiedOn",
                        "Direction": "1"
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

        stream_name = "LeadSquareLeadsData"
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
        stream_name = "LeadSquareLeadsData"
        request_host = config['leadsquare-host']
        access_key = config['leadsquare-access-key']
        secret_key = config['leadsquare-secret-key']
        start_timestamp_string = config['backfiller-start-timestamp'] if 'backfiller-start-timestamp' in config else None
        end_timestamp_string = config['backfiller-end-timestamp'] if 'backfiller-end-timestamp' in config else None
        if start_timestamp_string and end_timestamp_string:
            start_timestamp = datetime.strptime(start_timestamp_string, '%Y-%m-%d %H:%M:%S')
            end_timestamp = datetime.strptime(end_timestamp_string, '%Y-%m-%d %H:%M:%S')
            if start_timestamp > end_timestamp:
                raise Exception('Start timestamp cannot be greater than end timestamp')
        else:
            # Get current datetime in UTC
            current_datetime = datetime.now(timezone.utc)
            # Get the minute and round it down to the nearest 15th minute interval
            current_minute = current_datetime.minute
            rounded_minute = (current_minute // 15) * 15
            current_start_hour_timestamp = current_datetime.replace(minute=rounded_minute, second=0, microsecond=0)
            start_timestamp = current_start_hour_timestamp - timedelta(hours=1)
            end_timestamp = current_start_hour_timestamp
        
        print('start_timestamp', start_timestamp.strftime('%Y-%m-%d %H:%M:%S'), 'end_timestamp', end_timestamp.strftime('%Y-%m-%d %H:%M:%S'))
        page_index = 1
        error_count = 0
        while True:
            try:
                leadsquare_response = requests.post(
                    url=f'{request_host}/v2/LeadManagement.svc/Leads.RecentlyModified',
                    params={
                        "accessKey": access_key,
                        "secretKey": secret_key,
                    },
                    json={
                        "Parameter": {
                            "FromDate": start_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "ToDate": end_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        },
                        "Columns": {
                            "Include_CSV": ','.join(self.required_fields),
                        },
                        "Paging": {
                            "PageIndex": page_index,
                            "PageSize": 1000
                        },
                        "Sorting": {
                            "ColumnName": "ModifiedOn",
                            "Direction": "1"
                        }
                    }
                )
                if 200 <= leadsquare_response.status_code < 300:
                    leadsquare_response_json = leadsquare_response.json()
                    record_count = leadsquare_response_json['RecordCount']
                    if record_count == 0:
                        logger.info(f'|||||||||||No more leads to fetch. Exiting||||||||||||')
                        break
                    leadsquare_leads = leadsquare_response_json['Leads']
                    for leadsquare_lead in leadsquare_leads:
                        lead_data = {
                            lead_property if lead_property!= 'ProspectID' else 'ProspectId' : self.get_lead_property_from_leadsquare_lead(lead_property, leadsquare_lead) 
                            for lead_property in self.required_fields
                        }
                        yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(stream=stream_name, data=lead_data, emitted_at=int(datetime.now().timestamp()) * 1000),
                        )
                else:
                    error_count+=1
                    if error_count > 10:
                        break
                    else:
                        logger.error(f'LeadSquare Response Threw {leadsquare_response.status_code} with {leadsquare_response.status_code}')
                        time.sleep(5)
                        continue
                time.sleep(5)
                page_index += 1
            except Exception as e:
                logger.error(f'Error while running activity query: {str(e)}')
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
