#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_instahyre_job_scrapper import SourceInstahyreJobScrapper

if __name__ == "__main__":
    source = SourceInstahyreJobScrapper()
    launch(source, sys.argv[1:])
