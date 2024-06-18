#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
from datetime import datetime
from typing import Dict, Generator
import requests
import string
import random
import re

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


class SourceGlassdoorJobScrapper(Source):

    max_jobs_size = 50

    @staticmethod
    def extract_parameters(job_url):
        pattern = r'([a-zA-Z0-9-]+)-([a-zA-Z0-9_,]+)\.htm'
        match = re.match(pattern, job_url)
        job_title = "" 
        param = ""

        if match:
            job_title = match.group(1)
            param = match.group(2)
        
        return {
            "param": param,
            "job": job_title,
            "title": ' '.join(job_title.split("-")[:-1]),
            "url": f"https://www.glassdoor.co.in/Job/{job_url}",
        }
    
    @staticmethod
    def generate_random_string(length):
        characters = string.ascii_letters + string.digits + string.punctuation
        random_string = ''.join(random.choice(characters) for _ in range(length))

        return random_string

    def request(self, job_url, cursor=""):
        job_param = self.extract_parameters(job_url)
        url = "https://www.glassdoor.co.in/graph"
        payload = json.dumps([
        {
            "operationName": "JobSearchResultsQuery",
            "variables": {
                "keyword": job_param["title"],
                "locationId": 0,
                "numJobsToShow": 30,
                "originalPageUrl": job_param["url"],
                "parameterUrlInput": job_param["param"],
                "pageType": "SERP",
                "queryString": "",
                "seoFriendlyUrlInput": job_param["job"],
                "seoUrl": True,
                "pageCursor": cursor,
            },
            "query": "query JobSearchResultsQuery($excludeJobListingIds: [Long!], $filterParams: [FilterParams], $keyword: String, $locationId: Int, $locationType: LocationTypeEnum, $numJobsToShow: Int!, $originalPageUrl: String, $pageCursor: String, $pageNumber: Int, $pageType: PageTypeEnum, $parameterUrlInput: String, $queryString: String, $seoFriendlyUrlInput: String, $seoUrl: Boolean) {\n  jobListings(\n    contextHolder: {queryString: $queryString, pageTypeEnum: $pageType, searchParams: {excludeJobListingIds: $excludeJobListingIds, keyword: $keyword, locationId: $locationId, locationType: $locationType, numPerPage: $numJobsToShow, pageCursor: $pageCursor, pageNumber: $pageNumber, filterParams: $filterParams, originalPageUrl: $originalPageUrl, seoFriendlyUrlInput: $seoFriendlyUrlInput, parameterUrlInput: $parameterUrlInput, seoUrl: $seoUrl, searchType: SR}}\n  ) {\n    companyFilterOptions {\n      id\n      shortName\n      __typename\n    }\n    filterOptions\n    indeedCtk\n    jobListings {\n      ...JobView\n      __typename\n    }\n    jobListingSeoLinks {\n      linkItems {\n        position\n        url\n        __typename\n      }\n      __typename\n    }\n    jobSearchTrackingKey\n    jobsPageSeoData {\n      pageMetaDescription\n      pageTitle\n      __typename\n    }\n    paginationCursors {\n      cursor\n      pageNumber\n      __typename\n    }\n    indexablePageForSeo\n    searchResultsMetadata {\n      searchCriteria {\n        implicitLocation {\n          id\n          localizedDisplayName\n          type\n          __typename\n        }\n        keyword\n        location {\n          id\n          shortName\n          localizedShortName\n          localizedDisplayName\n          type\n          __typename\n        }\n        __typename\n      }\n      footerVO {\n        countryMenu {\n          childNavigationLinks {\n            id\n            link\n            textKey\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      helpCenterDomain\n      helpCenterLocale\n      jobAlert {\n        jobAlertExists\n        __typename\n      }\n      jobSerpFaq {\n        questions {\n          answer\n          question\n          __typename\n        }\n        __typename\n      }\n      jobSerpJobOutlook {\n        occupation\n        paragraph\n        heading\n        __typename\n      }\n      showMachineReadableJobs\n      __typename\n    }\n    serpSeoLinksVO {\n      relatedJobTitlesResults\n      searchedJobTitle\n      searchedKeyword\n      searchedLocationIdAsString\n      searchedLocationSeoName\n      searchedLocationType\n      topCityIdsToNameResults {\n        key\n        value\n        __typename\n      }\n      topEmployerIdsToNameResults {\n        key\n        value\n        __typename\n      }\n      topEmployerNameResults\n      topOccupationResults\n      __typename\n    }\n    totalJobsCount\n    __typename\n  }\n}\n\nfragment JobView on JobListingSearchResult {\n  jobview {\n    header {\n      adOrderId\n      advertiserType\n      ageInDays\n      divisionEmployerName\n      easyApply\n      employer {\n        id\n        name\n        shortName\n        __typename\n      }\n      organic\n      employerNameFromSearch\n      goc\n      gocConfidence\n      gocId\n      isSponsoredJob\n      isSponsoredEmployer\n      jobCountryId\n      jobLink\n      jobResultTrackingKey\n      normalizedJobTitle\n      jobTitleText\n      locationName\n      locationType\n      locId\n      needsCommission\n      payCurrency\n      payPeriod\n      payPeriodAdjustedPay {\n        p10\n        p50\n        p90\n        __typename\n      }\n      rating\n      salarySource\n      savedJobId\n      seoJobLink\n      __typename\n    }\n    job {\n      descriptionFragments\n      importConfigId\n      jobTitleId\n      jobTitleText\n      listingId\n      __typename\n    }\n    jobListingAdminDetails {\n      cpcVal\n      importConfigId\n      jobListingId\n      jobSourceId\n      userEligibleForAdminJobDetails\n      __typename\n    }\n    overview {\n      shortName\n      squareLogoUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
        }
        ])
        headers = {
            'authority': 'www.glassdoor.co.in',
            'accept': '*/*',
            'accept-language': 'en-GB,en;q=0.9',
            'apollographql-client-name': 'job-search-next',
            'apollographql-client-version': '7.15.4',
            'content-type': 'application/json',
            'gd-csrf-token': self.generate_random_string(20),
            'origin': 'https://www.glassdoor.co.in',
            'referer': 'https://www.glassdoor.co.in/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            return response.json()
        
        return {}

    def job_retreiver(self, job_url, cursor=""):
        page_response = self.request(job_url=job_url, cursor="")
        if len(page_response) > 0:
            return page_response[0] \
                    .get('data') \
                    .get('jobListings') \
                    .get('jobListings')
        return []
    
    def paginator_retreiver(self, job_url, cursor=""):
        page_response = self.request(job_url=job_url, cursor="")
        if len(page_response) > 0:
            return page_response[0] \
                    .get('data') \
                    .get('jobListings') \
                    .get('paginationCursors')
        return []

    def total_paginator_cursor(self, job_url):
        page_set = set()
        cursor = ""
        while len(page_set) < self.max_jobs_size:
            current_page_set_size = len(page_set)
            retreiver_page_list = self.paginator_retreiver(job_url=job_url, cursor=cursor)
            for retreiver_page in retreiver_page_list:
                page_set.add(retreiver_page.get('cursor'))
            
            if current_page_set_size == page_set:
                break
        
        return list(page_set)

    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        try:
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        from .streams_schema import stream_schema
        return AirbyteCatalog(streams=stream_schema)

    def read(
        self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        from .job_roles import job_roles

        for job_type in job_roles:
            for job_url in job_roles[job_type]:
                try:
                    total_paginated_cursor = self.total_paginator_cursor(job_url=job_url)

                    for paginated_cursor in total_paginated_cursor:
                        for job_details in self.job_retreiver(job_url=job_url, cursor=paginated_cursor):
                            individual_details = job_details.get('jobview').get('header')
                            individual_job_details = job_details.get('jobview').get('job')

                            company = {
                                "name": individual_details.get('employer').get('shortName')
                            }
                            yield AirbyteMessage(
                                    type=Type.RECORD,
                                    record=AirbyteRecordMessage(
                                            stream='companies', data=company, emitted_at=int(datetime.now().timestamp()) * 1000
                                    )
                            )
                            job_openings = {
                                "job_role": job_type,
                                "job_title": individual_details.get('jobTitleText'),
                                "job_location": individual_details.get('locationName'),
                                "job_source": "glassdoor",
                                "company": company.get("name"),
                                "job_description_raw_text": individual_job_details.get("descriptionFragments"),
                                "job_description_url_without_job_id": individual_details.get('seoJobLink'),
                                "job_description_url": individual_details.get('seoJobLink')
                            }

                            yield AirbyteMessage(
                                type=Type.RECORD,
                                record=AirbyteRecordMessage(
                                        stream='job_openings', data=job_openings, emitted_at=int(datetime.now().timestamp()) * 1000
                                ),
                            )
                except Exception as e:
                    print("Getting error white extracting server", e)
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
