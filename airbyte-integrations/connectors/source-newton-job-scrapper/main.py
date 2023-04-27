#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_newton_job_scrapper import SourceJobScrapper

if __name__ == "__main__":
    source = SourceJobScrapper()
    launch(source, sys.argv[1:])
