#!/bin/bash

sudo systemctl stop caserverapi.service
sudo systemctl disable caserverapi.service

sudo rm /etc/systemd/system/caserverapi.service

for filename in requirements.txt caserverapi.py caserverapi.sh venv
do
	sudo rm -r /etc/caserverapi/$filename
done

sudo mv /etc/caserverapi/server.key .
sudo mv /etc/caserverapi/server.crt .
sudo mv /etc/caserverapi/easy-rsa .

if [ "`ls /etc/caserverapi`" = "" ]
then
	rm -r /etc/caserverapi
fi

echo ""
echo ""
echo "CA Server API Service remove.sh complete."

for filename in server.key server.crt easy-rsa
do
	echo "Your ${filename} is at $(pwd)/${filename}."
done

echo "If you don't need then, please delete then."
