# Paperspider-manyusers 

`paperspider-manyusers` is a python based spider program designed for researchers especially for physicist. With the buildin schedulers, articles informations (from APS, Arxiv and etc.) are collected, label with `user_preference` and email to users. 

## Highlight

- Well defined database model to store informations of articles and user preferences. 
- Runing as daemon process. 

## Usage

To get start:
1. Config preferences in `config.py`
2. `python3 server.py [start|stop|restart]`, this will generate a daemon PID file `spiderd.pid` with the process id in it. 


## Config

In `config.py`, there should define `sender`, `tags` and `users`. `sender` is an email account used to deliver spider results. `tags` are a collect of tag used to label papers. `users` are a collect of user. A user have its email address and personal preference. 

**sender**: In `self.sender`. smtp server and a email account used to deliver spider results. 

**tags**: In `set_tags`. A tag is defined as

```python
def set_tags(self):
    _tag = Tag(self.conn, 'Tag:topo') # A tag_name used to label papers
    _tag.db_creat()
    _tag.dict = ['topological', 'weyl', 'semimetal'] # keywords of this tag
    self.tags.append(_tag)
    
    ...
```

**users**: In `set_users`. A user is defined as

```python
def set_users(self):
    _user = User(self.conn, 'jincao') # user name
    _user.db_creat()
    _user.email = 'caojin.phy@gmail.com' # spider results will send to this email address
    _tags = ['APS:selected', 'Tag:topo', 'Tag:twist', 'Tag:response'] # tag_name list, used to calculate user_preference
    _user.pair_tags(_tags, mode='update')
    self.users.append(_user)
```

## Dependency

- sqlite3
- requests
- bs4
- smtplib (smtp)
- python-daemon 
- apscheduler (scheduler)
- pytz
- ~~python-Levenshtein* (natural language processing)~~
