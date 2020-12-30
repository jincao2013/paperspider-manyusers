# Paperspider-manyusers 

`paperspider-manyusers` is a python based spider program designed for researchers especially for physicist. With the buildin schedulers, articles informations (from APS, Arxiv and etc.) are collected, label with `user_preference` and email to users. 

## Highlight

- We have designed a TAG system with a list of keywords to describe it 
- Support many-users mode
- Runing as system daemon process

## Usage

To get start:
1. set path of database in config.json
2. set path of log in config.json
3. set user preferences in config.json
4. python3 server.py <path_of_config.json> 

This will link to a existed database or creating a new one.

To run as a system daemon, copy the `./service.d/papaerspider.service` to `/etc/systemd/system`, 
and enable it. 

## Dependency

- sqlite3
- requests
- bs4
- smtplib (smtp)
- python-daemon 
- apscheduler (scheduler)
- pytz
- ~~python-Levenshtein* (natural language processing)~~
