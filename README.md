# Paperspider-ManyUsers 

This code helps you track updates from arXiv, Physical Review, Nature, and its sub-journals. The collected papers will be tagged with keywords configured by users. It can send updates via email. A Hacker News style web GUI is provided as well. Have fun! 

## Usage

For new installations:

1. Initialize the database using: `sqlite3 /opt/paperspider-db/sciDB.sqlite < init_sciDB.sql`
2. Configure `config.json`
3. Run `sudo bash install.sh`

## Dependencies

- sqlite3
- requests
- bs4
- smtplib (smtp)
- apscheduler (scheduler)
- pytz
- flask
