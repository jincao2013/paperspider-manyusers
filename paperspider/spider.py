# Copyright Jin Cao
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The paperspider code is hosted on GitHub:
#
# https://github.com/jincao2013/paperspider-manyusers

__date__ = "Feb. 7, 2020"

# import os
# import sys
# import sqlite3
# import logging
# import re
import time
from datetime import datetime, timedelta
import random
import numpy as np
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
# from selenium import webdriver
# from selenium.webdriver.firefox.service import Service as firefoxservice
# from webdriver_manager.firefox import GeckoDriverManager
from paperspider.dbAPI import Paper, Mailing_list
from paperspider.dbAPI import keyword_matching

'''
  * Sender
'''
class Sender(object):

    def __init__(self, user, password, smtp_server, smtp_port=25, ssl=True):
        # email of sender
        self.user = user
        self.password = password
        # SMTP server of sender
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.ssl = ssl

    def send_email(self, receiver, title, content_head, content):
        message = MIMEMultipart('alternative')
        message['From'] = self.user  # Header(self.user, 'utf-8')
        message['To'] = receiver  # Header(receiver, 'utf-8')
        message['Subject'] = Header(title, 'utf-8')

        message.attach(MIMEText(content_head + content, 'html', 'utf-8'))
        # message.attach(MIMEText(content, 'html', 'utf-8'))

        if self.ssl:
            smtp = smtplib.SMTP_SSL(self.smtp_server)
        else:
            smtp = smtplib.SMTP()

        smtp.connect(self.smtp_server, self.smtp_port)  # default port 25 for smtp (unsafe)

        # smtp.ehlo(smtpserver)
        smtp.login(self.user, self.password)
        smtp.sendmail(self.user, receiver, message.as_string())
        smtp.quit()

'''
  * PaperSpider objects
'''
class PaperSpider(object):

    def __init__(self, config):
        self.config = config
        self.enable_log = config.enable_log
        if self.enable_log: self.logger = config.logger
        self.conn = config.conn
        self.c = self.conn.cursor()
        self.enable_sender = config.enable_sender
        self.sender = config.sender

        # self.journal_url = None
        self.journal_name = None
        # self.interval_update = 24 # hours

        self.user_names = [i.name for i in config.users]
        self.user_emails = [i.email for i in config.users]
        self.num_users = config.num_users

        self.num_items = 0
        self.papers = []   # []
        self.papers_html = []
        # self.userinfos = []  # [(username, email), ...]
        self.preference_matrix = []  # [num_users, num_items]
        self.email_count = []

        self.keywords = self.config.keywords
        self.num_keywords = len(self.keywords)
        self.keyword_counts_matrix = None # [num_iterms, num_keywords]
        self.keywords_of_papers = []
        self.score_by_keywords = [] # [num_iterms]

    @staticmethod
    def get_html(journal_url):
        response = requests.get(journal_url)
        # print(response.status_code)
        while response.status_code == 403:
            time.sleep(500 + random.uniform(0, 500))
            response = requests.get(journal_url)
            # print(response.status_code)
        # print(response.status_code)
        if response.status_code == 200:
            return response.text
        return None

    def get_items(self):
        """
          tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'public_date']
          items = [head_StrID, url, ...]
        """
        tabletitle, items = [], []
        raise NotImplementedError

    def main(self, sendemail=True):
        # empty data for every cron job
        self.num_items = 0
        self.papers = []  # []
        self.papers_html = []
        self.preference_matrix = []  # [num_users * num_items]
        self.email_count = []

        self.keyword_counts_matrix = None # [num_iterms, num_keywords]
        self.keywords_of_papers = []
        self.score_by_keywords = [] # [num_iterms]

        # get papers from journal website
        tabletitle, items = self.get_items()
        for _, item in enumerate(items):
            head_StrID = item[0]
            ''' drop this item if it exists in the database '''
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(head_StrID)).fetchall()) != 0:
                continue

            ''' continue if not in database '''
            self.papers.append(Paper(self.conn, head_StrID))    # creat an empty Paper instance with only head_StrID
            _paper = self.papers[self.num_items]
            _paper.db_creat()              # creat a database entry
            for name, value in zip(tabletitle, item):
                _paper.__setattr__(name, value) # add details (in item) of this entry
            self.num_items += 1

        ''' report today's update in log '''
        # print("self.num_items =", self.num_items)
        if self.num_items == 0:
            if self.enable_log: self.logger.info('No update today.')
            return
        if self.enable_log: self.logger.info('{} new papers'.format(self.num_items))

        ''' cal keywords and score_by_keywords of today's papers '''
        self.keyword_counts_matrix = np.zeros([self.num_items, self.num_keywords])
        self.score_by_keywords = np.zeros([self.num_items])
        for ip in range(self.num_items):
            _paper = self.papers[ip]
            _content = _paper.authors + ' ' + _paper.title + ' ' + _paper.abstract + ' ' + _paper.note
            self.keyword_counts_matrix[ip] = np.array([_content.lower().count(keyword.lower()) for keyword in self.keywords])
            keywords_idx = np.where(self.keyword_counts_matrix[ip]>0.5)[0].tolist()
            self.keywords_of_papers.append('; '.join([self.keywords[idx] for idx in keywords_idx]))
            self.score_by_keywords[ip] = np.sum(self.keyword_counts_matrix[ip])
            _paper.keywords = self.keywords_of_papers[ip]
            _paper.score_by_keywords = self.score_by_keywords[ip]

        ''' assign tags to each papers and compute preference for each users of each papers (preferece matrix) '''
        [i.pair_tags() for i in self.papers] # assign tag for today's paper
        self.preference_matrix = np.array([i.compute_all_users_preferences(self.user_names) for i in self.papers]).T # [num_users * num_items]
        self.papers_html = [i.get_html() for i in self.papers]
        self.papers_html = [self.papers[i].get_html(self.keywords_of_papers[i], self.score_by_keywords[i]) for i in range(self.num_items)]

        self.update_mailing_list()
        if sendemail and self.enable_sender:
            self.send_emails()

    def update_mailing_list(self):
        sorted_idx = np.argsort(self.score_by_keywords)[::-1]
        selected_idx = np.where(np.array(self.score_by_keywords) > 0.5)[0]
        selected_sorted_idx = sorted_idx[np.isin(sorted_idx, selected_idx)]

        list_paper_idx = [self.papers[i].id for i in selected_sorted_idx]
        list_paper_stridx = [self.papers[i].head_StrID for i in selected_sorted_idx]

        if 'arXiv' in self.journal_name:
            subject = 'arXiv'
        elif 'Phys. Rev. B' in self.journal_name:
            subject = 'PRB'
        elif 'Phys. Rev. Lett.' in self.journal_name:
            subject = 'PRL'
        elif 'Phys. Rev. Research' in self.journal_name:
            subject = 'PRRes'
        elif 'Phys. Rev. X' in self.journal_name:
            subject = 'PRX'
        elif 'Nature Communications' in self.journal_name:
            subject = 'Nat_Commun'
        elif 'Nature Nanotechnology' in self.journal_name:
            subject = 'Nat_Nanotechnol'
        elif 'Nature Materials' in self.journal_name:
            subject = 'Nat_Mater'
        elif 'Nature Physics' in self.journal_name:
            subject = 'Nat_Phys'
        else:
            subject = self.journal_name

        mailing_list = Mailing_list(self.conn)
        mailing_list.db_creat(subject, list_paper_idx, list_paper_stridx)
        if self.enable_log: self.logger.info('added {} ({} papers) to mailing list'.format(subject, len(list_paper_idx)))

    def send_emails(self):
        self.email_count = [0 for i in range(self.num_users)]
        content_head = """
        <p>
        Dear subscriber, <br/>
        Here attached recent updated papers on <mark>{}</mark>.  <br/>
        Best,  <br/>
        PaperSpider <br/>
        </p>

        """.format(self.journal_name)
        title = '[Paper Spider] New Articles'
        contents = ''

        ''' prepare email for user, and sort the order by keyword_counts_matrix '''
        sorted_idx = np.argsort(self.score_by_keywords)[::-1]
        selected_idx = np.where(self.preference_matrix[0] > 0.5)[0]
        selected_sorted_idx = sorted_idx[np.isin(sorted_idx, selected_idx)]

        idx_user = 0
        self.email_count[idx_user] = len(selected_sorted_idx)
        for ip in selected_sorted_idx:
            contents[idx_user] += self.papers_html[ip]
        contents = """
        <div style="width: 70%">
            <ol>
        """ + contents + """
            </ol>
        </div>
        """

        # with open('test_email.html', 'a') as f:
        #     f.write(contents[i])

        ''' send email to user '''
        if self.email_count[idx_user] > 0:
            if self.enable_log: self.logger.info('email {} new articals to {}'.format(self.email_count[idx_user], self.user_names[idx_user]))
            # self.send_email(self.user_emails[i], contents[i])
            self.sender.send_email(self.user_emails[idx_user], title, content_head, contents)
            time.sleep(random.random() * 60 * 1)
        else:
            if self.enable_log: self.logger.info('email no articals to {}'.format(self.user_names[idx_user]))

'''
  * arXiv spider
'''
class Arxiv(PaperSpider):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'arXiv cond-mat'
        # self.time_update = 24 # hours

    def get_items(self):
        tabletitle, items_mes_hall = self.get_items_mes_hall()
        tabletitle, items_mtrl_sci = self.get_items_mtrl_sci()

        unique_items = {}
        for item in items_mes_hall + items_mtrl_sci:
            item_id = item[0]
            unique_items[item_id] = item
        items = list(unique_items.values())

        return tabletitle, items

    def get_items_mes_hall(self):
        # debug
        # with open('./arXiv1.html', 'r') as f:
        #     raw_html = f.read()
        # soup = BeautifulSoup(raw_html, features='html.parser')
        journal_url = 'https://arxiv.org/list/cond-mat.mes-hall/new'
        soup = BeautifulSoup(self.get_html(journal_url), features='html.parser')
        content = soup.find('div', id='dlpage')
        current_date_us = datetime.now() - timedelta(hours=12)
        date = current_date_us.strftime("%A, %d %B %Y")

        list_ids = content.find_all('a', title='Abstract')
        list_title = content.find_all('div', class_='list-title mathjax')
        list_authors = content.find_all('div', class_='list-authors')
        list_abstract = content.find_all('p', class_='mathjax')
        list_abstract = [i.text.replace('\n', ' ') for i in list_abstract]

        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'public_date']
        items = []
        num_papers = len(list_ids)
        for i in range(num_papers):
            items.append([
                list_ids[i].text.strip(), # head_StrID
                r'https://arxiv.org'+list_ids[i].attrs['href'], # url
                list_title[i].text, # title
                list_authors[i].text, # authors
                '', # note
                list_abstract[i], # abstract
                'preprint', # version
                'arXiv cond-mat.mes-hall', # journal
                date, # journal
            ])
        return tabletitle, items

    def get_items_mtrl_sci(self):
        # debug
        # with open('./arXiv2.html', 'r') as f:
        #     raw_html = f.read()
        # soup = BeautifulSoup(raw_html, features='html.parser')
        journal_url = 'https://arxiv.org/list/cond-mat.mtrl-sci/new'
        soup = BeautifulSoup(self.get_html(journal_url), features='html.parser')
        content = soup.find('div', id='dlpage')
        current_date_us = datetime.now() - timedelta(hours=12)
        date = current_date_us.strftime("%A, %d %B %Y")

        list_ids = content.find_all('a', title='Abstract')
        list_title = content.find_all('div', class_='list-title mathjax')
        list_authors = content.find_all('div', class_='list-authors')
        list_abstract = content.find_all('p', class_='mathjax')
        list_abstract = [i.text.replace('\n', ' ') for i in list_abstract]

        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'public_date']
        items = []
        num_papers = len(list_ids)
        for i in range(num_papers):
            items.append([
                list_ids[i].text.strip(), # head_StrID
                r'https://arxiv.org'+list_ids[i].attrs['href'], # url
                list_title[i].text, # title
                list_authors[i].text, # authors
                '', # note
                list_abstract[i], # abstract
                'preprint', # version
                'arXiv cond-mat.mtrl-sci', # journal
                date, # journal
            ])
        return tabletitle, items

'''
  * APS Spider 
    - Due to Cloudflare protection, we are using RSS feeds instead, see https://journals.aps.org/feeds
    - In these RSS feeds: 
      PRL: updates about 0~5 papers per day, showing papers from the last 30 days (100 papers)
      PRB: updates about 30 papers per day, showing papers from the last 7 days (100 papers)
      PRX: updates about 1 papers per day, showing papers from the last 90 days (100 papers)
      PRResearch: updates about 10 papers per day, showing papers from the last 7 days (100 papers)
'''
class Aps(object):

    def __init__(self):
        self.journal_url = 'https://journals.aps.org'
        self.journal_name = 'Phys. Rev.'
        self.journal_note = ''

class ApsPRL(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_url = r'http://feeds.aps.org/rss/tocsec/PRL-CondensedMatterStructureetc.xml'
        self.journal_name = 'Phys. Rev. Lett.'
        self.journal_note = 'PRL:Cond-mat'

    def get_items(self):
        tabletitle, _items = get_items_aps_from_rss(self.journal_name, self.journal_url, self.journal_note)
        items = []
        for i in _items:
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(i[0])).fetchall()) != 0:
                continue
            items.append(i)
        return tabletitle, items

class ApsPRX(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_url = r'http://feeds.aps.org/rss/recent/prx.xml'
        self.journal_name = 'Phys. Rev. X'
        self.journal_note = 'allPRX'

    def get_items(self):
        tabletitle, _items = get_items_aps_from_rss(self.journal_name, self.journal_url, self.journal_note)
        items = []
        for i in _items:
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(i[0])).fetchall()) != 0:
                continue
            items.append(i)
        return tabletitle, items

class ApsPRResearch(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_url = r'http://feeds.aps.org/rss/recent/prresearch.xml'
        self.journal_name = 'Phys. Rev. Research'
        self.journal_note = 'allPRResearch'

    def get_items(self):
        tabletitle, _items = get_items_aps_from_rss(self.journal_name, self.journal_url, self.journal_note)
        items = []
        for i in _items:
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(i[0])).fetchall()) != 0:
                continue
            items.append(i)
        return tabletitle, items

class ApsPRB(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_url = r'http://feeds.aps.org/rss/recent/prb.xml'
        self.journal_name = 'Phys. Rev. B'
        self.journal_note = 'allPRB'

    def get_items(self):
        tabletitle, _items = get_items_aps_from_rss(self.journal_name, self.journal_url, self.journal_note)
        items = []
        for i in _items:
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(i[0])).fetchall()) != 0:
                continue
            items.append(i)
        return tabletitle, items

def get_items_aps_from_rss(journal_name, journal_url, journal_note):
    # get current issue
    response = requests.get(journal_url)
    soup = BeautifulSoup(response.text, "xml")
    content_select = soup.find_all('item')

    # parse the results
    items = []
    tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'volume',
                  'issue', 'public_date']

    list_title = [i.find('title').text for i in content_select]
    list_url = [i.find('link').text for i in content_select]
    list_authors = [i.find('dc:creator').text for i in content_select]
    list_head_StrID = [i.find('prism:doi').text.split('/')[-1] for i in content_select]
    list_abstract = [i.find('description').text for i in content_select]
    list_version = ['published' for i in content_select]
    # list_note = [i.find('description').text.split('<p>')[1].split('</p>')[0] for i in content_select]
    list_note = [journal_note for i in content_select]
    list_journal = [journal_name for i in content_select]
    list_volume = [i.find('prism:volume').text for i in content_select]
    list_issue = [i.find('prism:number').text for i in content_select]
    list_public_date = [i.find('prism:publicationDate').text.split('T')[0] for i in content_select]

    _zip = zip(list_head_StrID, list_url, list_title, list_authors, list_note, list_abstract,
               list_version, list_journal, list_volume, list_issue, list_public_date)
    for i, item in enumerate(_zip):
        items.append(item)

    return tabletitle, items

'''
  * Nature spider
    - look up physical-sciences of nature and its subjournals, see https://www.nature.com/nature/browse-subjects
'''
class Nature(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature'
        self.journal_url = r'https://www.nature.com/subjects/condensed-matter-physics/nature'
        self.journal_note = 'All_Nat' # add to tag to receive all papers from Nature
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Physics(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Physics'
        self.journal_url = r'https://www.nature.com/subjects/condensed-matter-physics/nphys'
        self.journal_note = 'All_Nat_Phys' # add to tag to receive all papers from Nat. Phys.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Materials(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Materials'
        self.journal_url = r'https://www.nature.com/subjects/condensed-matter-physics/nmat'
        self.journal_note = 'All_Nat_Mater' # add to tag to receive all papers from Nat. Mater.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Nanotechnology(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Nanotechnology'
        self.journal_url = r'https://www.nature.com/subjects/condensed-matter-physics/nnano'
        self.journal_note = 'All_Nat_Nanotechnol' # add to tag to receive all papers from Nat. Nanotechnol.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Communications(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Communications'
        self.journal_url = r'https://www.nature.com/subjects/condensed-matter-physics/ncomms'
        self.journal_note = 'All_Nat_Comm' # add to tag to receive all papers from Nat. Comm.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

def get_items_nature(journal_name, journal_url, journal_note):
    blacklist = [
        'dark energy', 'universe', 'planet', 'moon', 'galaxy', 'mars', 'thermonuclear', 'big bang', 'stars',
        'cataly', 'reactant',
        'health', 'cancer'
    ]

    items = []
    tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'public_date']

    response = requests.get(journal_url)
    soup = BeautifulSoup(response.text, features='html.parser')
    content = soup.find('div', id='content').find('section', class_="u-container").find_all('article')

    for i in content:
        head_StrID = i.find('a').get('href')[1:]
        _title = i.find('a').text.strip()
        try:
            _abstract = i.find('div', itemprop="description").find('p').text
        except AttributeError:
            _abstract = ''
        try:
            _authors = i.find_all('span', itemprop="name")[0].text
        except IndexError:
            _authors = ''

        ''' ignore if in blacklist '''
        relevancy = keyword_matching(blacklist, _abstract + ' ' + _title)
        if relevancy > 0.5: continue

        items.append([
            head_StrID,  # head_StrID
            "https://www.nature.com/" + head_StrID,  # url
            _title,  # title
            _authors,  # authors
            journal_note,  # note
            _abstract,  # abstract
            'published',
            journal_name,
            i.find('time', itemprop="datePublished").text,  # public_date
        ])

    return tabletitle, items

# def get_html_headless_firefox(url):
#     # Set up headless options for Firefox
#     options = webdriver.FirefoxOptions()
#     options.add_argument("--headless")  # Run in headless mode
#
#     # Create a new instance of the Firefox driver
#     driver = webdriver.Firefox(service=firefoxservice(GeckoDriverManager().install()), options=options)
#
#     # Go to the desired URL
#     driver.get(url)
#
#     # driver.title == 'Just a moment...'
#
#     # Get the page source
#     html_content = driver.page_source
#     return html_content

'''
  * etc.
'''
def echo_time(int_time=None):
    if int_time is None:
        _int_time = time.time()
    else:
        _int_time = int_time
    return time.strftime("%b.%d,%Y; %a; %H:%M:%S", time.localtime(_int_time))

class TempSpider(PaperSpider):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_url = 'https://journals.aps.org'

    def get_items(self):
        """
          * tabletitle = ['head_StrID', ...]
            items = [item1, ...]
        """  #
        tabletitle, items = [], []
        raise NotImplementedError

if __name__ == "__main__":
    pass
    # conn = sqlite3.connect('sciDB.sqlite')
    # c = conn.cursor()

    # self.url = 'https://arxiv.org/list/cond-mat.mes-hall/new?show=10'
    # html = self.get_html()

    # html = open('./test/arxiv_tmp.html').read()
    # soup = BeautifulSoup(html, features='html.parser')
    #
    #
    # self = Arxiv(conn)
    # self.main()
    # self.send_emails()
    # # conn.close()

    # journal_url = 'https://journals.aps.org'
    # journal_name = 'Phys. Rev. Research'
    # journal_note = 'PRResearch:selected'
    # aps_subjects_label_concerned = {
    #     'Condensed Matter Physics',
    #     'Strongly Correlated Materials',
    #     'Materials Science',
    #     'Computational Physics',
    #     'Superconductivity',
    #     'Topological Insulators',
    #     'Magnetism',
    #     'Graphene',
    # }
    # xhr_headers = {
    #     'x-requested-with': 'XMLHttpRequest',
    # }
