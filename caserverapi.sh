#!/bin/bash

workdir="/etc/caserverapi"

. ./venv/bin/activate

gunicorn --bind 0.0.0.0:80 --chdir easy-rsa caserverapi:app

