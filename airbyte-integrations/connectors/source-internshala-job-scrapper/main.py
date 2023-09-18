#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_internshala_job_scrapper import SourceInternshalaJobScrapper

if __name__ == "__main__":
    source = SourceInternshalaJobScrapper()
    launch(source, sys.argv[1:])
