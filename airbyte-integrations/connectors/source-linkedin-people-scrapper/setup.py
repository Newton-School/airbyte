#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    "airbyte-cdk~=0.2",
    "bs4~=0.0.1",
    "selenium~=4.9.0",
    "sqlalchemy==2.0.1"
]

TEST_REQUIREMENTS = [
    "pytest~=6.2",
    "connector-acceptance-test",
]

setup(
    name="source_linkedin_people_scrapper",
    description="Source implementation for Linkedin People Scrapper.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
