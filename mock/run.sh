#!/bin/sh
#
# Script for running the mock Case web service.
# The process is started in the background. Use Ctrl + C to terminate.
#
# Usage: run.sh
#
# Author: John Topley (john.topley@ons.gov.uk)
#
nohup bundle exec rackup -p 8171 ./caseservice/config.ru &
case_pid=$!

# Trap SIGINTs so we can send them back to $case_pid.
trap "kill -2 $case_pid" 2

# In the meantime, wait for $case_pid to end.
wait $case_pid
