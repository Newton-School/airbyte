import requests
import json

url = "https://www.glassdoor.co.in/graph"

# payload = json.dumps([
#   {
#     "operationName": "JobSearchResultsQuery",
#     "variables": {
#       "excludeJobListingIds": [],
#       "filterParams": [],
#       "keyword": "analyst-jobs",
#       "locationId": 0,
#       "numJobsToShow": 30,
#       "originalPageUrl": "https://www.glassdoor.co.in/Job/analyst-jobs-SRCH_KO0,7.htm",
#       "parameterUrlInput": "KO0,7",
#       "pageType": "SERP",
#       "queryString": "",
#       "seoFriendlyUrlInput": "analyst-jobs",
#       "seoUrl": True,
#       "pageCursor": "AB4ACoEBLAAAAAAAAAAAAAAAAiTjAlwBKgEJAUGEAQYODSwHEgcsBjQGcgcWBgKjBs85Z0WxZqoqjytQ37R6Hxrfxnm9sfc1mCFH1xH7jfFkLy/GXYbQIYgllVd9MhVOOsI89Zst8HfYEbiLvVL9s7eHWm21oVraoSsZ4bryyNZsxWWRsQVoRh+OtoDWOM2Ci6I/jIQSFQBi/X8wUySn+JbgkOWrN1PtvQosYNJQRWn0ArbNCgpr/TQ5tXgqSLoHZS9ZBMxIMSNhnM5MvXYIg2MkSbULMC9Rqxsubpg2bIo9TK5vPEbeUfCVGgnWTNx394AEOIybfmmscP0zAAnaaFJkulUwXx50YVZ8e7Y4c02cEYO/4BGYgTaUrLAPeBgQ0nglx2mhsXf/9qOY7sHAKBmk+ahU+Ce52FaYYX+dj72svHkAAA==",
#     },
#     "query": "query JobSearchResultsQuery($excludeJobListingIds: [Long!], $filterParams: [FilterParams], $keyword: String, $locationId: Int, $locationType: LocationTypeEnum, $numJobsToShow: Int!, $originalPageUrl: String, $pageCursor: String, $pageNumber: Int, $pageType: PageTypeEnum, $parameterUrlInput: String, $queryString: String, $seoFriendlyUrlInput: String, $seoUrl: Boolean) {\n  jobListings(\n    contextHolder: {queryString: $queryString, pageTypeEnum: $pageType, searchParams: {excludeJobListingIds: $excludeJobListingIds, keyword: $keyword, locationId: $locationId, locationType: $locationType, numPerPage: $numJobsToShow, pageCursor: $pageCursor, pageNumber: $pageNumber, filterParams: $filterParams, originalPageUrl: $originalPageUrl, seoFriendlyUrlInput: $seoFriendlyUrlInput, parameterUrlInput: $parameterUrlInput, seoUrl: $seoUrl, searchType: SR}}\n  ) {\n    companyFilterOptions {\n      id\n      shortName\n      __typename\n    }\n    filterOptions\n    indeedCtk\n    jobListings {\n      ...JobView\n      __typename\n    }\n    jobListingSeoLinks {\n      linkItems {\n        position\n        url\n        __typename\n      }\n      __typename\n    }\n    jobSearchTrackingKey\n    jobsPageSeoData {\n      pageMetaDescription\n      pageTitle\n      __typename\n    }\n    paginationCursors {\n      cursor\n      pageNumber\n      __typename\n    }\n    indexablePageForSeo\n    searchResultsMetadata {\n      searchCriteria {\n        implicitLocation {\n          id\n          localizedDisplayName\n          type\n          __typename\n        }\n        keyword\n        location {\n          id\n          shortName\n          localizedShortName\n          localizedDisplayName\n          type\n          __typename\n        }\n        __typename\n      }\n      footerVO {\n        countryMenu {\n          childNavigationLinks {\n            id\n            link\n            textKey\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      helpCenterDomain\n      helpCenterLocale\n      jobAlert {\n        jobAlertExists\n        __typename\n      }\n      jobSerpFaq {\n        questions {\n          answer\n          question\n          __typename\n        }\n        __typename\n      }\n      jobSerpJobOutlook {\n        occupation\n        paragraph\n        heading\n        __typename\n      }\n      showMachineReadableJobs\n      __typename\n    }\n    serpSeoLinksVO {\n      relatedJobTitlesResults\n      searchedJobTitle\n      searchedKeyword\n      searchedLocationIdAsString\n      searchedLocationSeoName\n      searchedLocationType\n      topCityIdsToNameResults {\n        key\n        value\n        __typename\n      }\n      topEmployerIdsToNameResults {\n        key\n        value\n        __typename\n      }\n      topEmployerNameResults\n      topOccupationResults\n      __typename\n    }\n    totalJobsCount\n    __typename\n  }\n}\n\nfragment JobView on JobListingSearchResult {\n  jobview {\n    header {\n      adOrderId\n      advertiserType\n      ageInDays\n      divisionEmployerName\n      easyApply\n      employer {\n        id\n        name\n        shortName\n        __typename\n      }\n      organic\n      employerNameFromSearch\n      goc\n      gocConfidence\n      gocId\n      isSponsoredJob\n      isSponsoredEmployer\n      jobCountryId\n      jobLink\n      jobResultTrackingKey\n      normalizedJobTitle\n      jobTitleText\n      locationName\n      locationType\n      locId\n      needsCommission\n      payCurrency\n      payPeriod\n      payPeriodAdjustedPay {\n        p10\n        p50\n        p90\n        __typename\n      }\n      rating\n      salarySource\n      savedJobId\n      seoJobLink\n      __typename\n    }\n    job {\n      descriptionFragments\n      importConfigId\n      jobTitleId\n      jobTitleText\n      listingId\n      __typename\n    }\n    jobListingAdminDetails {\n      cpcVal\n      importConfigId\n      jobListingId\n      jobSourceId\n      userEligibleForAdminJobDetails\n      __typename\n    }\n    overview {\n      shortName\n      squareLogoUrl\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"
#   }
# ])
# headers = {
#   'authority': 'www.glassdoor.co.in',
#   'accept': '*/*',
#   'accept-language': 'en-GB,en;q=0.9',
#   'apollographql-client-name': 'job-search-next',
#   'apollographql-client-version': '7.15.4',
#   'content-type': 'application/json',
#   'gd-csrf-token': 'drumil',
#   'origin': 'https://www.glassdoor.co.in',
#   'referer': 'https://www.glassdoor.co.in/',
#   'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
# }

# response = requests.request("POST", url, headers=headers, data=payload)

# json_response = response.json()[0].get('data').get('jobListings').get('jobListings')

# for jre in json_response:
#   print(json.dumps(jre, indent=4))


from job_roles import job_roles

for key in job_roles:
  print(key)