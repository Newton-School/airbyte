#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#


from setuptools import find_packages, setup

MAIN_REQUIREMENTS = [
    "airbyte-cdk~=1.3",
]

TEST_REQUIREMENTS = [
    "pytest~=6.2",
    "connector-acceptance-test",
]

setup(
    name="source_leadsquare_activities",
    description="Source implementation for Leadsquare Activities.",
    author="Airbyte",
    author_email="contact@airbyte.io",
    packages=find_packages(),
    install_requires=MAIN_REQUIREMENTS,
    package_data={"": ["*.json", "*.yaml"]},
    extras_require={
        "tests": TEST_REQUIREMENTS,
    },
)
