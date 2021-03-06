#!/usr/bin/env bash
set -e

ras_rm_repo_url=$1
if [ -d tmp_ras_rm_docker_dev ]; then
    echo "tmp_ras_rm_docker_dev exists";
else
    git clone --depth 1 ${ras_rm_repo_url} tmp_ras_rm_docker_dev;
fi;
pushd tmp_ras_rm_docker_dev
make down
popd
rm -rf tmp_ras_rm_docker_dev