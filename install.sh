#!/usr/bin/bash

sudo cp -rf paperspider-db /opt

sudo mkdir -f /etc/paperspider
sudo cp config.json /etc/paperspider

sudo cp service.d/paperspider.service /etc/systemd/system
sudo systemctl load paperspider.service
sudo systemctl start paperspider.service

