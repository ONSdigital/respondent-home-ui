EQ_RUNNER_REPO_URL = https://github.com/ONSdigital/eq-survey-runner.git
RAS_RM_REPO_URL = https://github.com/ONSdigital/ras-rm-docker-dev.git
RM_TOOLS_REPO_URL = https://github.com/ONSdigital/rm-tools.git

.PHONY: test unit_tests integration_tests

install:
	pipenv install --dev

test: start_services wait_for_services setup integration_tests stop_services

start_services:
	./start_ras_rm.sh ${RAS_RM_REPO_URL}
	./start_eq.sh ${EQ_RUNNER_REPO_URL}

stop_services:
	./stop_ras_rm.sh ${RAS_RM_REPO_URL}
	./stop_eq.sh ${EQ_RUNNER_REPO_URL}

wait_for_services:
	pipenv run python wait_for_services.py

setup:
	./setup_data.sh ${RM_TOOLS_REPO_URL}

integration_tests:
	pipenv run python integration_tests.py