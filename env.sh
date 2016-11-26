#!/bin/sh
#
# Script for setting the required environment variables in development.
# Adjust as required.
#
# Usage: source ./env.sh
#
# Author: John Topley (john.topley@ons.gov.uk)
#
export RESPONDENT_HOME_ANALYTICS_ACCOUNT="UA-56892037-7"
export RESPONDENT_HOME_EQ_HOST="eq-server"
export RESPONDENT_HOME_EQ_PORT="5000"
export RESPONDENT_HOME_EQ_PROTOCOL="http"
export RESPONDENT_HOME_IAC_ATTEMPTS_EXPIRATION_SECS="30"
export RESPONDENT_HOME_IAC_SERVICE_HOST="localhost"
export RESPONDENT_HOME_IAC_SERVICE_PORT="8121"
export RESPONDENT_HOME_LOCALE="en"
export RESPONDENT_HOME_MAX_IAC_ATTEMPTS="100"
export RESPONDENT_HOME_REDIS_HOST="localhost"
export RESPONDENT_HOME_REDIS_PORT="6379"
export RESPONDENT_HOME_REDIS_PASSWORD="redis"
