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


class SourceLeadsquareUsers(Source):
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

            leadsquare_response = requests.get(
                url=f'{request_host}/v2/UserManagement.svc/Users.Get',
                params={
                    "accessKey": access_key,
                    "secretKey": secret_key,
                },
            )

            if 200 <= leadsquare_response.status_code < 300:
                return AirbyteConnectionStatus(status=Status.SUCCEEDED)

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
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
        user_fields = {
            "userId": {
                "type": "string"
            },
            "firstName": {
                "type": "string",
            },
            "lastName": {
                "type": "string"
            },
            "emailAddress": {
                "type": "string"
            },
            "role": {
                "type": "string"
            },
            "statusCode": {
                "type": "number"
            },
            "tag": {
                "type": ["string", "null"]
            },
            "isPhoneCallAgent": {
                "type": "boolean",
                "default": False
            },
        }

        stream_name = "LeadSquareUsers"

        json_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": user_fields,
        }

        streams = [
            {
                "name": stream_name,
                "supported_sync_modes": [
                    "full_refresh",
                    "incremental"
                ],
                "source_defined_cursor": True,
                ""
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
        stream_name = "LeadSquareUsers"

        try:
            request_host = config['leadsquare-host']
            access_key = config['leadsquare-access-key']
            secret_key = config['leadsquare-secret-key']

            leadsquare_response = requests.get(
                url=f'{request_host}/v2/UserManagement.svc/Users.Get',
                params={
                    "accessKey": access_key,
                    "secretKey": secret_key,
                },
            )

            if 200 <= leadsquare_response.status_code < 300:
                for leadsquare_users in leadsquare_response.json():

                    data = {
                        "userId": leadsquare_users["ID"],
                        "firstName": leadsquare_users["FirstName"],
                        "lastName": leadsquare_users["LastName"],
                        "emailAddress": leadsquare_users["EmailAddress"],
                        "role": leadsquare_users["Role"],
                        "statusCode": leadsquare_users["StatusCode"],
                        "tag": leadsquare_users["Tag"],
                        "isPhoneCallAgent": leadsquare_users["IsPhoneCallAgent"],
                    }

                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream=stream_name, data=data, emitted_at=int(datetime.now().timestamp()) * 1000),
                    )

            else:
                logger.error(f'LeadSquare Response Threw {leadsquare_response.status_code} with {leadsquare_response.status_code}')
        except Exception as e:
            logger.error(f'Error while running activity query: {str(e)}')

