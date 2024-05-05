# Paperspider-ManyUsers 

`paperspider-manyusers`  is designed for researchers in physical sciences. Equipped with built-in TAG system and schedulers, this program gathers article information timely and efficiently from reputable sources such as APS, Nature (and its sub-journals), and arXiv. The collected data is then categorized with predefined tags and distributed to users via email. 

## Highlight

- Tag system to follow update of papers from Physical Review, Nature, and arXiv
- Multi-user support

## Usage

For new installations:

1. Initialize the database using SQLite3: `/opt/paperspider-db/sciDB.sqlite < init_sciDB.sql`
2. Configure `config.json`
3. Run `sudo bash install.sh`

## Dependencies

- sqlite3
- requests
- bs4
- smtplib (smtp)
- apscheduler (scheduler)
- pytz
