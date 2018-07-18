#!/usr/bin/env bash
set -e

rm_tools_repo_url=$1
echo "Setting up initial data required for integration tests"
if [ -d tmp_rm_tools ]; then
    echo "tmp_rm_tools exists - pulling";
    cd tmp_rm_tools; git pull; cd -;
else
    git clone -b social-test-setup --depth 1 --single-branch ${rm_tools_repo_url} tmp_rm_tools;
fi;
cp setup.env tmp_rm_tools/social-test-setup/.env
cp tests/test_data/sample/social-survey-sample.csv tmp_rm_tools/social-test-setup/data/
pushd tmp_rm_tools/social-test-setup
pipenv install
make setup-and-execute
popd
rm -rf tmp_rm_tools
echo "Integration tests can now be run"