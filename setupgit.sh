#!/bin/bash
cd /tmp

rm -r CA-server-api

git clone https://github.com/NCKU-NASA/CA-server-api

cd CA-server-api

for a in $(ls -a)
do
    if [ "$a" != "." ] && [ "$a" != ".." ] && [ "$a" != ".git" ] && [ "$a" != "Readme.md" ] && [ "$a" != "install.sh" ] && [ "$a" != "remove.sh" ] && [ "$a" != "setupgit.sh" ] && [ "$a" != "config.yaml" ]
    then
        rm -rf $a
    fi
done

for a in $(ls -a /etc/caserverapi)
do
    if [ "$a" != "." ] && [ "$a" != ".." ] && [ "$a" != "config.yaml" ] && [ "$(cat /etc/caserverapi/.gitignore | sed 's/\/.*//g' | sed '/^!.*/d' | grep -P "^$(echo "$a" | sed 's/\./\\\./g')$")" == "" ]
    then
        sudo cp -r /etc/caserverapi/$a $a
    fi
done

sudo cp /usr/local/bin/caserverapi caserverapi.sh
sudo cp /etc/systemd/system/caserverapi.service caserverapi.service
