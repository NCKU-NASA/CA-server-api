#!/bin/bash

workdir="/etc/caserverapi"

. ./venv/bin/activate

cd easy-rsa

gunicorn --bind [::]:80 caserverapi:app

