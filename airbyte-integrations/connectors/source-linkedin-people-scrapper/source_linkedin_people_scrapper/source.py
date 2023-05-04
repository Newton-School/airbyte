#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
import os
from datetime import datetime
from typing import Dict, Generator
from sqlalchemy import create_engine, MetaData, Table

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
import re
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from airbyte_cdk.sources import Source
import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.NOTSET)

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.getenv("CHROME_BIN")
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-browser-side-navigation')
chrome_options.add_argument('--disable-infobars')
chrome_options.add_argument('--disable-extensions')

driver = webdriver.Chrome(executable_path=os.getenv("CHROME_DRIVER_PATH"), options=chrome_options)


class SourceLinkedinPeopleScrapper(Source):
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
            # Not Implemented

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
        from .streams_schema import stream_schema

        return AirbyteCatalog(streams=stream_schema)


    # def fetch_linkedin_links_for_pending(self, companies):
    #     for name in companies:


    @staticmethod
    def pending_urls(db_password, db_host):
        company_names = []
        engine = create_engine(f'postgresql://airbyte_user:{db_password}@{db_host}:5432/job_postings')

        metadata = MetaData()
        companies = Table("companies", metadata, autoload_with=engine)

        query = companies.select().where(companies.c.linkedin_url.is_(None))
        with engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                company_names.append(row[0])
        return company_names

    @staticmethod
    def infinite_scroll(url, scroll_times, button_class_name, driver_required=True):
        if driver_required:
            driver.get(url)
        time.sleep(2)
        scroll_times = scroll_times
        for i in range(scroll_times):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                if driver_required:
                    button = WebDriverWait(driver, 0).until(
                        EC.presence_of_element_located((By.CLASS_NAME, button_class_name)))
                    button.click()
                else:
                    button = WebDriverWait(driver, 0).until(EC.element_to_be_clickable((By.CLASS_NAME, button_class_name)))
                    button.click()
            except:
                pass
            time.sleep(1)

        html = driver.page_source
        if driver_required:
            driver.close()
        return html

    @staticmethod
    def get_scroll_time_count_using_selenium(url, denominator):
        driver.get(url)
        time.sleep(2)
        div_element = driver.find_element("css selector", ".org-grid__content-height-enforcer")
        h2_element = div_element.find_element("css selector", "h2")
        results_text = h2_element.text
        numeric_part = re.findall(r'\d+', results_text)[0]
        return int(int(numeric_part) / denominator)

    def search_people_from_company(self, company_url, keyword):
        people_details = dict()
        final_url = f"{company_url}/people/?keywords={keyword}"
        scroll_times = self.get_scroll_time_count_using_selenium(final_url, denominator=12)
        html = self.infinite_scroll(
            final_url, scroll_times,
            driver_required=False,
            button_class_name="scaffold-finite-scroll__load-button"
        )

        soup = BeautifulSoup(html, 'html.parser')
        div_tag = soup.find("div", class_=lambda x: x and "scaffold-finite-scroll__content" in x.split())
        ul_element = div_tag.find_all('ul')[0]

        li_tags = ul_element.find_all("li")
        for li in li_tags:
            try:
                profile_url = li.find('a', class_='app-aware-link')['href']
                name = li.find('div',
                               class_='ember-view lt-line-clamp lt-line-clamp--single-line org-people-profile-card__profile-title t-black') \
                    .text.strip()
                description = li.find(
                    'div', class_='ember-view lt-line-clamp lt-line-clamp--multi-line'
                ).text.strip()
                people_details['linkedin_profile_url'] = profile_url
                people_details['name'] = name
                people_details['short_intro'] = description
            except:
                pass
        time.sleep(2)
        return people_details

    @staticmethod
    def login_to_linkedin(username, password):
        driver.get("https://www.linkedin.com/login")
        driver.find_element("xpath", """//*[@id="username"]""").send_keys(username)
        driver.find_element("xpath", """//*[@id="password"]""").send_keys(password)
        driver.find_element("xpath", """//*[@id="organic-div"]/form/div[3]/button""").click()
        time.sleep(1)

    @staticmethod
    def get_company_urls(db_host, db_password):
        company_urls = {}
        engine = create_engine(f'postgresql://airbyte_user:{db_password}@{db_host}:5432/job_postings')

        metadata = MetaData()
        companies = Table("companies", metadata, autoload_with=engine)

        query = companies.select().where(companies.c.linkedin_url.isnot(None))
        with engine.connect() as conn:
            result = conn.execute(query)
            for row in result:
                company_urls[row[1]] = row[0]
        return company_urls

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
        company_urls = self.get_company_urls(config['db_host'], config['db_password'])

        self.login_to_linkedin(username=config['username'], password=config['password'])

        keywords = ['IT%20Recruiter%20India', 'Human%20Resources%20India']

        for company_url, company_name in company_urls.items():
            for keyword in keywords:
                try:
                    people_details = self.search_people_from_company(company_url, keyword)
                    people_details['company'] = company_name
                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream='recruiter_details', data=people_details,
                                                    emitted_at=int(datetime.now().timestamp()) * 1000),
                    )
                except:
                    pass
