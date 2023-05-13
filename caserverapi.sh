#!/bin/bash

workdir="/etc/caserverapi"

cd $workdir

. ./venv/bin/activate

gunicorn --bind $(yq e '.ListenHost' config.yaml):$(yq e '.ListenPort' config.yaml) --chdir easy-rsa main:app

