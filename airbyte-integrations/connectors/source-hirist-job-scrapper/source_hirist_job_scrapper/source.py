#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
import requests
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
from airbyte_protocol.models import AirbyteStateMessage, AirbyteStateType, AirbyteStreamState, StreamDescriptor

from airbyte_cdk.sources import Source


class SourceHiristJobScrapper(Source):
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
            url = f"https://jobseeker-api.hirist.com/v2/jobfeed/-1/v3/search?pageNo=1&query=" \
            f"{'Angular Developer'}&loc=&minexp=0&maxexp=2&range=0&boost=1"
            requests.get(url).json()
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema

        return AirbyteCatalog(streams=stream_schema)

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
        import requests
        from .job_roles import job_roles
        counter = 0
        for query in job_roles:
            has_more = True
            page_no = 0
            while has_more:
                url = f"https://jobseeker-api.hirist.com/v2/jobfeed/-1/v3/search?pageNo={page_no}&query=" \
                        f"{query}&loc=&minexp=0&maxexp=2&range=0&boost=1"
                try:
                    resp = requests.get(url).json()
                except Exception as e:
                    print(str(e))
                    break
                jobs = resp.get('jobs') or []

                for job in jobs:
                    skills = {"preferredSkills": [], "otherSkills": []}
                    tags = job.get('tags') or []
                    for tag in tags:
                        skill_name = tag.get('name')
                        is_mandatory = tag.get('isMandatory')
                        if is_mandatory:
                            skills['preferredSkills'].append(skill_name)
                        else:
                            skills['otherSkills'].append(skill_name)

                    locations = job.get('locations')

                    location_name = locations[0].get('name') if locations else ""

                    company_data = job.get('companyData')
                    if company_data:
                        company_name = company_data.get('companyName')
                        company = {
                            "name": company_name
                        }

                        yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='companies', data=company, emitted_at=int(datetime.now().timestamp()) * 1000
                                )
                        )
                    else:
                        company_name = ""

                    job_opening = {
                        "job_role": query,
                        "job_title": job.get('title') or "",
                        "min_experience": str(job.get('min')) or "",
                        "max_experience": str(job.get('max')) or "",
                        "job_description_url": job.get('jobDetailUrl') or "",
                        "skills": skills,
                        "min_ctc": str(job.get('minSal')) or "",
                        "max_ctc": str(job.get('maxSal')) or "",
                        "company": company_name,
                        "job_source": "hirist",
                        "job_location": location_name,
                        "raw_response": job,
                        "job_description_url_without_job_id": job.get('id') or "",
                        "job_description_raw_text": job.get('introText') or ""
                    }

                    yield AirbyteMessage(
                            type=Type.RECORD,
                            record=AirbyteRecordMessage(
                                    stream='job_openings', data=job_opening, emitted_at=int(datetime.now().timestamp()) * 1000
                            ),
                    )

                    recruiter = job.get('recruiter')
                    if recruiter:
                        recruiter_details = {
                            "hiring_manager_for_job_link": job.get('jobDetailUrl'),
                            "name": recruiter.get('recruiterName'),
                            "company": company_name,
                            "short_intro": recruiter.get('designation'),
                            "linkedin_profile_url": f"dummy_{company_name}"
                        }
                        yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='recruiter_details', data=recruiter_details,
                                        emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                        )

                has_more = resp.get('hasMore')
                page_no += 1
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