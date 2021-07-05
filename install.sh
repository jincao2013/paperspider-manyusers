#!/usr/bin/bash

sudo cp -rf * /opt/paperspider
sudo mv /opt/paperspider/paperspider-db /opt/paperspider-db

sudo mkdir -f /etc/paperspider
sudo cp config.json /etc/paperspider

sudo cp service.d/paperspider.service /etc/systemd/system
sudo systemctl enable paperspider.service
sudo systemctl stop paperspider.service
sudo systemctl start paperspider.service

