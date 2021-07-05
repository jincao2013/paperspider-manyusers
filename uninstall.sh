#!/usr/bin/bash

sudo systemctl stop paperspider.service
sudo systemctl disable paperspider.service
sudo rm -f /etc/systemd/system/paperspider.service

sudo rm -rf /opt/paperspider-db 
sudo rm -rf /opt/paperspider

sudo rm /etc/paperspider/config.json
