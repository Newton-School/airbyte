#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_glassdoor_job_scrapper import SourceGlassdoorJobScrapper

if __name__ == "__main__":
    source = SourceGlassdoorJobScrapper()
    launch(source, sys.argv[1:])
