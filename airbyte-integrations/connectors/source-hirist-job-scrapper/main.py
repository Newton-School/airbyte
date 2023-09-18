#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_hirist_job_scrapper import SourceHiristJobScrapper

if __name__ == "__main__":
    source = SourceHiristJobScrapper()
    launch(source, sys.argv[1:])
