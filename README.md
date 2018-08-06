# Respondent Home Python Web Application
Respondent Home is part of ONS's Survey Data Collection platform. It allows users to validate their Internet Access Code (IAC) and forwards
them to the [ONS eQ Survey Runner](https://github.com/ONSdigital/eq-survey-runner) upon successful validation.

![The ONS Survey Data Collection platform](/images/sdc_platform.png?raw=true)

This repository contains the Python [AIOHTTP](http://docs.aiohttp.org/en/stable/) application that is the user interface for the Respondent Home product.

## Payload

The fields required to launch an eQ survey is documented in the [ons-schema-definitions](http://ons-schema-definitions.readthedocs.io/en/latest/respondent_management_to_electronic_questionnaire.html#required-fields).

Currently, the only social survey that is targeted is LMS 1. The full schema of which exists in the eQ Survey Runner repository [here](https://github.com/ONSdigital/eq-survey-runner/blob/master/data/en/lms_1.json).

## Installation
Install the required Python packages for running and testing Respondent Home within a virtual environment:

  `make install`

## Running
To run this application in development use:

  `make run`

and access using [http://localhost:9092](http://localhost:9092).

## Tests
To run the unit tests for Respondent Home:

  `make unittests`

To bring up all the RAS/RM & eQ Runner services and run the integration tests against them and Respondent Home:

  `make test`

NB: Waiting for the services to be ready will likely take up to ten minutes.

## Docker
Respondent Home is one part of the RAS/RM docker containers:

  [https://github.com/ONSdigital/ras-rm-docker-dev](https://github.com/ONSdigital/ras-rm-docker-dev)

## Environment Variables
The environment variables below must be provided:

```
JSON_SECRET_KEYS
SECRET_KEY
```
