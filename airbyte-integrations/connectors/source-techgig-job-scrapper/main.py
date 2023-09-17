#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_techgig_job_scrapper import SourceTechgigJobScrapper

if __name__ == "__main__":
    source = SourceTechgigJobScrapper()
    launch(source, sys.argv[1:])
