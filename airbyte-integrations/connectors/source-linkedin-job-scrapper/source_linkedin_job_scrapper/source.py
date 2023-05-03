#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import json
import os
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
import re
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
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
job_type_keys = {
    "full_time": "F",
    "part_time": "P"
}
past_time_keys = {
    "second": "r60",
    "day": "r86400",
    "week": "r604800",
    "month": "r2592000"
}
job_level_keys = {
    "internship": 1,
    "entry_level": 2,
    "associate": 3,
    "mid_senior_level": 4,
    "director": 5
}


class SourceLinkedinJobScrapper(Source):
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
            return AirbyteConnectionStatus(status=Status.SUCCEEDED)
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"An exception occurred: {str(e)}")

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:

        from .streams_schema import stream_schema

        return AirbyteCatalog(streams=stream_schema)

    @staticmethod
    def create_soup(url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

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

    def get_scroll_time_count(self, url, tag_name, class_name, denominator):
        soup = self.create_soup(url)
        tag = soup.find(tag_name, class_=class_name)
        results_text = tag.text
        numeric_part = re.findall(r'\d+', results_text)[0]
        if int(numeric_part) == 1:
            tag2 = soup.find(tag_name, class_='results-context-header__new-jobs')
            results_text2 = tag2.text
            results_text2 = results_text2.replace(',', '')
            numeric_part2 = re.findall(r'\d+', results_text2)[0]
            return int(int(numeric_part2) / denominator)
        return int(int(numeric_part) / denominator)

    @staticmethod
    def get_scroll_time_count_using_selenium(url, denominator):
        driver.get(url)
        time.sleep(2)
        div_element = driver.find_element("css selector", ".org-grid__content-height-enforcer")
        h2_element = div_element.find_element("css selector", "h2")
        results_text = h2_element.text
        numeric_part = re.findall(r'\d+', results_text)[0]
        return int(int(numeric_part) / denominator)

    @staticmethod
    def login_to_linkedin(username, password):
        driver.get("https://www.linkedin.com/login")
        driver.find_element("xpath", """//*[@id="username"]""").send_keys(username)
        driver.find_element("xpath", """//*[@id="password"]""").send_keys(password)
        driver.find_element("xpath", """//*[@id="organic-div"]/form/div[3]/button""").click()
        time.sleep(1)

    def get_all_jobs_jd_links(self, job_role="Software%20Engineer", location="India", job_type="full_time", past_time="day",
                              job_level="entry_level"):
        jd_links = set()
        job_search_base_url = "https://www.linkedin.com/jobs/search?"
        final_url = job_search_base_url
        payload = {
            "keywords": job_role,
            "location": location,
            "f_JT": job_type_keys[job_type],
            "f_TPR": past_time_keys[past_time],
            "f_E": job_level_keys[job_level]
        }

        for key, val in payload.items():
            final_url += f"{key}={val}&"
        scroll_times = self.get_scroll_time_count(final_url, tag_name='span', class_name="results-context-header__job-count",
                                                  denominator=25)
        html = self.infinite_scroll(final_url, scroll_times, button_class_name="infinite-scroller__show-more-button--visible")

        soup = BeautifulSoup(html, 'html.parser')
        ul_tag = soup.find("ul", class_="jobs-search__results-list")
        li_tags = ul_tag.find_all("li")

        for li in li_tags:
            a_tags = li.find_all("a")
            for a in a_tags:
                if "base-card__full-link" in a.get("class", []):
                    jd_links.add(a['href'].split("?")[0])
        return jd_links

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

    def read(
            self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:

        company_urls = dict()

        job_role = config['job_role']

        job_role_data = {'title': job_role}
        yield AirbyteMessage(
            type=Type.RECORD,
            record=AirbyteRecordMessage(stream='job_roles', data=job_role_data, emitted_at=int(datetime.now().timestamp()) * 1000),
        )

        for jd_link in self.get_all_jobs_jd_links(job_role=job_role):
            job_details = {
                'job_description_url': jd_link,
                'job_description_url_without_job_id': jd_link,
                'job_role': job_role
            }
            try:
                jd_link = jd_link.replace("https://in.", "https://www.")
                soup = self.create_soup(jd_link)
                company_details = {}

                h1_tag = soup.find("h1", class_="top-card-layout__title")
                if h1_tag:
                    job_details['job_title'] = h1_tag.text

                company_span_tags = soup.find_all("span", class_=lambda x: x and "topcard__flavor" in x.split())
                for span in company_span_tags:
                    a_tag = span.find("a")
                    if a_tag:
                        text = a_tag.text.strip()
                        href = a_tag.get("href")
                        company_details['name'] = text
                        company_details['linkedin_url'] = str(href).split("?")[0]
                        company_urls.update({str(href).split("?")[0]: text})

                details_span_tags = soup.find_all("span", class_=lambda x: x and "topcard__flavor--bullet" in x.split())
                span_texts = []
                for span in details_span_tags:
                    span_texts.append(span.text.strip())
                if len(span_texts) == 1:
                    job_details['job_location'] = span_texts[0]
                if len(span_texts) == 2:
                    job_details['job_location'] = span_texts[0]
                    job_details['raw_response'] = {'applicants': span_texts[1]}

                div_tags = soup.find_all("div", class_=lambda x: x and "show-more-less-html__markup" in x.split())
                for div in div_tags:
                    html_content = div.decode_contents()
                    text_soup = BeautifulSoup(html_content.strip(), "html.parser")
                    job_details['job_description_raw_text'] = text_soup

                ul_tag = soup.find("ul", class_=lambda x: x and "description__job-criteria-list" in x.split())
                li_tags = ul_tag.find_all("li")
                for li in li_tags:
                    h3_tag = li.find("h3")
                    h3_text = h3_tag.get_text(strip=True) if h3_tag else ""
                    span_tag = li.find("span")
                    span_text = span_tag.get_text(strip=True) if span_tag else ""
                    job_details[h3_text] = span_text

                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(stream='companies', data=company_details, emitted_at=int(datetime.now().timestamp()) * 1000),
                )

                job_details = job_details | {
                    'company': company_details['name'],
                    'job_source': 'linkedin',
                    'job_type': 'full-time'
                }
            except:
                pass

                yield AirbyteMessage(
                    type=Type.RECORD,
                    record=AirbyteRecordMessage(stream='job_openings', data=job_details, emitted_at=int(datetime.now().timestamp()) * 1000),
                )

        self.login_to_linkedin(username=config['username'], password=config['password'])
        keywords = ['IT%20Recruiter%20India', 'Human%20Resources%20India']
        for company_url, company_name in company_urls.items():
            for keyword in keywords:
                try:
                    people_details = self.search_people_from_company(company_url, keyword)
                    people_details['company'] = company_name
                    people_details['keyword'] = keyword
                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream='recruiter_details', data=people_details,
                                                    emitted_at=int(datetime.now().timestamp()) * 1000),
                    )
                except:
                    pass
