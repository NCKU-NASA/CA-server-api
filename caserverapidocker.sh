#!/bin/bash

if [ $# -lt 1 ]
then
    echo "Usage: $0 <ca name>" 1>&2
    exit 1
fi

workdir="/usr/app"

cd $workdir

if [ -d mountpki ]
then
    if ! [ -f mountpki/ca.crt ]
    then
        easyrsa init-pki
        echo "$1" | easyrsa build-ca nopass
        easyrsa gen-crl
        mv pki/* mountpki
        rm -r pki
    fi
    ln -s mountpki pki
else
    easyrsa init-pki
    echo "$1" | easyrsa build-ca nopass
    easyrsa gen-crl
fi

gunicorn --bind $(yq e '.ListenHost' config.yaml):$(yq e '.ListenPort' config.yaml) main:app
