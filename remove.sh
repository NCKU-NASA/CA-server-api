#!/bin/bash

sudo systemctl stop caserverapi.service
sudo systemctl disable caserverapi.service

sudo rm /etc/systemd/system/caserverapi.service

for filename in requirements.txt main.py conf sign config.yaml venv .gitignore __pycache__
do
	sudo rm -r /etc/caserverapi/$filename
done

sudo rm /usr/local/bin/caserverapi

sudo mv /etc/caserverapi/server.key .
sudo mv /etc/caserverapi/server.crt .
sudo mv /etc/caserverapi/pki .

if [ "`ls /etc/caserverapi`" = "" ]
then
	rm -r /etc/caserverapi
fi

echo ""
echo ""
echo "CA Server API Service remove.sh complete."

for filename in server.key server.crt pki
do
	echo "Your ${filename} is at $(pwd)/${filename}."
done

echo "If you don't need then, please delete then."
