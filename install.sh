#!/usr/bin/bash

sudo mkdir -p /opt/paperspider
sudo cp -rf * /opt/paperspider/
sudo mv -rf /opt/paperspider/paperspider-db /opt/paperspider-db

sudo mkdir -p /etc/paperspider
sudo cp config.json /etc/paperspider/

sudo cp service.d/paperspider.service /etc/systemd/system
sudo systemctl enable paperspider.service
sudo systemctl stop paperspider.service
sudo systemctl start paperspider.service