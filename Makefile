EQ_RUNNER_REPO_URL = https://github.com/ONSdigital/eq-survey-runner.git
RAS_RM_REPO_URL = https://github.com/ONSdigital/ras-rm-docker-dev.git
RM_TOOLS_REPO_URL = https://github.com/ONSdigital/rm-tools.git

.PHONY: test unit_tests integration_tests

build: install

install:
	pipenv install --dev

serve:
	pipenv run inv server

run:
	pipenv run inv run

test: flake8 unittests

local_test:  start_services wait_for_services setup integration_tests stop_services

live_test: start_services wait_for_services setup live_integration_tests stop_services

start_services:
	./scripts/start_ras_rm.sh ${RAS_RM_REPO_URL}
	./scripts/start_eq.sh ${EQ_RUNNER_REPO_URL}

stop_services:
	./scripts/stop_ras_rm.sh ${RAS_RM_REPO_URL}
	./scripts/stop_eq.sh ${EQ_RUNNER_REPO_URL}

wait_for_services:
	pipenv run inv wait

setup:
	./scripts/setup_data.sh ${RM_TOOLS_REPO_URL}

integration_tests:
	pipenv run inv integration

live_integration_tests:
	pipenv run inv integration --live

unittests:
	pipenv run inv unittests

flake8:
	pipenv run inv flake8

demo:
	./scripts/start_eq.sh ${EQ_RUNNER_REPO_URL}
	pipenv run inv demo
