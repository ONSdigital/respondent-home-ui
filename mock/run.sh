#!/bin/sh
#
# Script for running the mock Internet Access Code web service.
# The process is started in the background. Use Ctrl + C to terminate.
#
# Usage: run.sh
#
# Author: John Topley (john.topley@ons.gov.uk)
#
nohup bundle exec rackup -p 8141 ./iacservice/config.ru &
iac_pid=$!

# Trap SIGINTs so we can send them back to $iac_pid.
trap "kill -2 $iac_pid" 2

# In the meantime, wait for $iac_pid to end.
wait $iac_pid
