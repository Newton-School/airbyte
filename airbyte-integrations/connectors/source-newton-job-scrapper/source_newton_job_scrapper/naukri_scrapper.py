import requests

class NaukriJobScrapper():
    def __init__(self):
        self.base_api_url = 'https://www.naukri.com/jobapi/v3'


    def scrape_jobs_from_naukri(self, job_type):
        job_opening_stream = 'job_openings'
        app_id = 110
        system_id = 110
        url = self.base_api_url + '/search?'

        for pageNo in range(1, 50):
            params = {
                'keyword': job_type,
                'pageNo': pageNo,
                'jobAge': 1,
                'noOfResults': 30,
                'searchType': 'adv'
            }
            naukriResponse = requests.get(url, params=params,
                headers={
                    'appid': app_id,
                    'systemid': system_id,
                })
            if 200 <= naukriResponse.status_code < 300:
                for jobObj in naukriResponse.json()['jobDetails']:
                    jobData = {
                        'jobId': jobObj['jobId'].strip(),
                        'title': jobObj['title'].strip(),
                        'jdUrl': "https://www.naukri.com" + jobObj['jdURL'].strip(),
                        'companyName': jobObj['companyName'].strip(),
                        'jdText': self.remove_html_tags(jobObj['jobDescription'].strip()),
                        'jobType': 'Not available',
                        'role': searchJobType,
                        'companyId': jobObj['companyId'].strip(),
                    }

                    internal_response = requests.get(
                        'https://www.naukri.com/jobapi/v4/job/' + jobObj['jobId'],
                        headers={
                            'appid': app_id,
                            'systemid': system_id,
                        })
                    internalObj = internal_response.json()['jobDetails']

                    internalData = {
                        'skills': {
                            'preferredSkills': self.get_labels(internalObj['keySkills']['preferred']),
                            'otherSkills': self.get_labels(internalObj['keySkills']['other']),
                        },
                        'department': internalObj['functionalArea'],
                        'employmentType': internalObj['employmentType'],
                        'relevancy': True if internalObj['maximumExperience'] <= 1 or internalObj['minimumExperience'] <= 1 else False,
                        'salary': internalObj['salaryDetail']['label'],
                        'extraDetails': internalObj,
                        'minimumExperience': internalObj['minimumExperience'],
                        'maximumExperience': internalObj['maximumExperience'],
                        'withoutJobId': self.updated_url(f"https://www.naukri.com{jobObj['jdURL']}", f"-{jobObj['jobId']}")
                    }

                    for placeholderObj in jobObj['placeholders']:
                        if (placeholderObj['type'] == 'location'):
                            internalData['location'] = placeholderObj['label'].strip()

                    jobData.update(internalData)

                    yield AirbyteMessage(
                        type=Type.RECORD,
                        record=AirbyteRecordMessage(stream=stream_name, data=jobData, emitted_at=int(datetime.now().timestamp()) * 1000),
                    )
            else:
                logger.error(f'Naukri Response Threw {naukriResponse.status_code} with {naukriResponse.status_code}')
