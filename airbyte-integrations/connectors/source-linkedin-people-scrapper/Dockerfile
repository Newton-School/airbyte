FROM python:3.9-alpine as base

# build and load all requirements
FROM base as builder
WORKDIR /airbyte/integration_code

RUN apk add --no-cache chromium

# upgrade pip to the latest version
RUN apk upgrade \
    && pip install --upgrade pip \
    && apk --no-cache add tzdata build-base


COPY setup.py ./
# install necessary packages to a temporary folder
RUN pip install --prefix=/install .

# build a clean environment
FROM base
WORKDIR /airbyte/integration_code

# copy all loaded and built libraries to a pure basic image
COPY --from=builder /install /usr/local
# add default timezone settings
COPY --from=builder /usr/share/zoneinfo/Etc/UTC /etc/localtime

RUN echo "Etc/UTC" > /etc/timezone

# bash is installed for more convenient debugging.
RUN apk --no-cache add bash

# copy payload code only
COPY main.py ./
COPY source_linkedin_people_scrapper ./source_linkedin_people_scrapper

ENV AIRBYTE_ENTRYPOINT "python /airbyte/integration_code/main.py"
ENTRYPOINT ["python", "/airbyte/integration_code/main.py"]

RUN apk add \
    dumb-init \
    chromium \
    chromium-chromedriver

ENV CHROME_BIN=/usr/lib/chromium/chrome \
    CHROME_DRIVER_PATH=/usr/lib/chromium/chromedriver

LABEL io.airbyte.version=0.1.0
LABEL io.airbyte.name=airbyte/source-linkedin-people-scrapper
