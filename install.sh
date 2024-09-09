#!/usr/bin/bash

sudo mkdir -p /opt/paperspider
sudo mkdir -p /opt/paperspider-db
sudo mkdir -p /etc/paperspider

sudo cp -rf * /opt/paperspider/
sudo cp config.json /etc/paperspider/
#sudo mv /opt/paperspider/paperspider-db /opt/paperspider-db

# Configure and start the service
sudo cp service.d/paperspider.service /etc/systemd/system
sudo cp service.d/paperspider_web.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable paperspider.service
sudo systemctl enable paperspider_web.service
sudo systemctl restart paperspider.service
sudo systemctl restart paperspider_web.service