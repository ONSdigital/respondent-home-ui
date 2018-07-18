#!/usr/bin/env bash
set -e

eq_repo_url=$1

if [ -d tmp_eq_docker_dev ]; then
    echo "tmp_eq_docker_dev exists - pulling";
    cd tmp_eq_docker_dev; git pull; cd -;
else
    git clone --depth 1 ${eq_repo_url} tmp_eq_docker_dev;
fi;
pushd tmp_eq_docker_dev
docker-compose pull
docker-compose up -d eq-survey-runner
popd