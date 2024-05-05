#!/usr/bin/bash

sudo mkdir -p /opt/paperspider
sudo cp -rf * /opt/paperspider/
#sudo mv /opt/paperspider/paperspider-db /opt/paperspider-db

sudo mkdir -p /etc/paperspider
sudo cp config.json /etc/paperspider/

# Configure and start the service
sudo cp service.d/paperspider.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable paperspider.service
sudo systemctl restart paperspider.service