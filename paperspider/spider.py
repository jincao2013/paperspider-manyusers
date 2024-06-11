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
import time
from datetime import datetime, timedelta
import random
# import sqlite3
# import logging
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from paperspider.dbAPI import Paper
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
        self.logger = config.logger
        self.conn = config.conn
        self.c = self.conn.cursor()
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
        self.score_by_keywords = None # [num_iterms]

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
          * tabletitle = ['head_StrID', ...]
            items = [item1, ...]
        """  #
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
        self.score_by_keywords = None # [num_iterms]

        tabletitle, items = self.get_items()
        for i, item in enumerate(items):
            head_StrID = item[0]
            ''' drop this item if it exists in the database '''
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(head_StrID)).fetchall()) != 0:
                continue

            ''' proceed if not in database '''
            self.papers.append(Paper(self.conn, head_StrID))
            self.papers[self.num_items].db_creat()
            for name, value in zip(tabletitle, item):
                self.papers[self.num_items].__setattr__(name, value)
            self.num_items += 1

        ''' report today's update in log '''
        if self.num_items == 0:
            self.logger.info('No update today.')
            return
        self.logger.info('{} new papers'.format(self.num_items))

        ''' cal keyword_counts_matrix '''
        self.keyword_counts_matrix = np.zeros([self.num_items, self.num_keywords])
        for ip in range(self.num_items):
            _paper = self.papers[ip]
            _content = _paper.authors + ' ' + _paper.title + ' ' + _paper.abstract + ' ' + _paper.note
            self.keyword_counts_matrix[ip] = np.array([_content.lower().count(keyword.lower()) for keyword in self.keywords])
            keywords_idx = np.where(self.keyword_counts_matrix[ip]>0.5)[0].tolist()
            self.keywords_of_papers.append(', '.join([self.keywords[idx] for idx in keywords_idx]))
        self.score_by_keywords = np.sum(self.keyword_counts_matrix, axis=1)

        ''' assign tags to each papers and compute preference for each users of each papers (preferece matrix) '''
        [i.pair_tags() for i in self.papers]
        self.preference_matrix = np.array([i.compute_all_users_preferences(self.user_names) for i in self.papers]).T # [num_users * num_items]
        self.papers_html = [i.get_html() for i in self.papers]
        self.papers_html = [self.papers[i].get_html(self.keywords_of_papers[i], self.score_by_keywords[i]) for i in range(self.num_items)]

        if sendemail:
            self.send_emails()

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
        contents = ['' for i in range(self.num_users)]
        for i in range(self.num_users):
            ''' prepare email for each user, and sort the order by keyword_counts_matrix '''
            sorted_idx = np.argsort(self.score_by_keywords)[::-1]
            selected_idx = np.where(self.preference_matrix[0] > 0.5)[0]
            selected_sorted_idx = sorted_idx[np.isin(sorted_idx, selected_idx)]

            self.email_count[i] = len(selected_sorted_idx)
            for ip in selected_sorted_idx:
                contents[i] += self.papers_html[ip]
            contents[i] = """
            <div style="width: 70%">
                <ol>
            """ + contents[i] + """
                </ol>
            </div>
            """

            # with open('test_email.html', 'a') as f:
            #     f.write(contents[i])

        ''' send email to users '''
        for i in range(self.num_users):
            if self.email_count[i] > 0:
                self.logger.info('email {} new articals to {}'.format(self.email_count[i], self.user_names[i]))
                # self.send_email(self.user_emails[i], contents[i])
                self.sender.send_email(self.user_emails[i], title, content_head, contents[i])
                time.sleep(random.random() * 60 * 1)
            else:
                self.logger.info('email no articals to {}'.format(self.user_names[i]))

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
'''
class Aps(object):

    def __init__(self):
        self.journal_url = 'https://journals.aps.org'
        self.journal_name = 'Phys. Rev.'
        self.journal_note = ''
        self.aps_subjects_label_concerned = {
            'Condensed Matter Physics',
            'Strongly Correlated Materials',
            'Materials Science',
            'Computational Physics',
            'Superconductivity',
            'Topological Insulators',
            'Magnetism',
            'Graphene',
        }
        self.xhr_headers = {
            'x-requested-with': 'XMLHttpRequest',
        }

class ApsPRL(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_name = 'Phys. Rev. Lett.'
        self.journal_note = 'PRL:Cond-mat'

    def get_items(self):
        journal_url = self.journal_url
        journal_name = self.journal_name
        journal_note = self.journal_note
        xhr_headers = self.xhr_headers

        # get current issue url
        response = requests.get(journal_url + '/prl')
        soup = BeautifulSoup(response.text, features='html.parser')
        current_issue_link = soup.find('a', id='current-issue-link').attrs.get('href')

        # get current issue
        items = []
        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'volume',
                      'issue', 'public_date']

        response = requests.get(journal_url + current_issue_link)
        soup = BeautifulSoup(response.text, "html.parser")

        vol_issue = soup.find('section', id='title').h2.text
        volume, issue = re.findall(r'\d+', vol_issue)

        content = soup.find('div', id='toc-content')
        content = content.find_all('section', class_='open')
        content_select = []
        for i in content:
            if 'Condensed Matter' in i.h4.text:
                content_select += i.find_all('div', class_='article panel article-result')

        list_data_id = [i.attrs['data-id'] for i in content_select]
        list_head_StrID = [i.split('/')[-1] for i in list_data_id]
        list_url = [journal_url + i.a.attrs['href'] for i in content_select]
        list_title = [i.a.text for i in content_select]
        list_authors = [i.find('h6', class_='authors').text for i in content_select]
        list_note = [journal_note for i in content_select]
        list_abstract = []
        list_version = ['published' for i in content_select]
        list_journal = [journal_name for i in content_select]
        list_volume = [volume for i in content_select]
        list_issue = [issue for i in content_select]
        list_public_date = [i.find('h6', class_='pub-info').text.split('Published')[-1].strip() for i in
                            content_select]

        with requests.Session() as session:
            for i in range(len(content_select)):
                if len(self.c.execute("select id from papers where head_StrID=:value", {'value': list_head_StrID[i]}).fetchall()) != 0:
                    list_abstract.append('Exist in db.')
                    continue
                _r = session.get(''.join([journal_url, '/_api/v1/articles/', list_data_id[i], '/abstract']), headers=xhr_headers)
                if _r.status_code == 200:
                    list_abstract.append(_r.text[3:-4])
                else:
                    list_abstract.append('ERROR in get abstract: <Response [{}]>'.format(_r.status_code))

        _zip = zip(list_head_StrID, list_url, list_title, list_authors, list_note, list_abstract,
                   list_version, list_journal, list_volume, list_issue, list_public_date)
        for i, item in enumerate(_zip):
            items.append(item)

        return tabletitle, items

class ApsPRX(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_name = 'Phys. Rev. X'
        self.journal_note = 'PRX:selected'

    def get_items(self):
        aps_subjects_label_concerned = self.aps_subjects_label_concerned
        journal_url = self.journal_url
        journal_name = self.journal_name
        journal_note = self.journal_note
        xhr_headers = self.xhr_headers

        # get current issue url
        response = requests.get(journal_url + '/prx')
        soup = BeautifulSoup(response.text, features='html.parser')
        current_issue_link = soup.find('a', id='current-issue-link').attrs.get('href')

        # get current issue
        items = []
        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'volume',
                      'issue', 'public_date']
        response = requests.get(journal_url + current_issue_link)
        soup = BeautifulSoup(response.text, "html.parser")

        vol_issue = soup.find('section', id='title').h2.text
        volume, issue = re.findall(r'\d+', vol_issue)

        content = soup.find('div', id='toc-content')
        content = content.find_all('div', class_='article-result')
        content_select = []
        for i in content:
            subjects_label = {j.text for j in i.find_all('a', class_='label')}
            # print(prx_subjects_label & prx_subjects_label_concerned)
            if len(subjects_label & aps_subjects_label_concerned) > 0:
                content_select.append(i)

        list_data_id = [i.attrs['data-id'] for i in content_select]
        list_head_StrID = [i.split('/')[-1] for i in list_data_id]
        list_url = [journal_url + i.a.attrs['href'] for i in content_select]
        list_title = [i.a.text for i in content_select]
        list_authors = [i.find('h6', class_='authors').text for i in content_select]
        list_note = [journal_note for i in content_select]
        list_abstract = []
        list_version = ['published' for i in content_select]
        list_journal = [journal_name for i in content_select]
        list_volume = [volume for i in content_select]
        list_issue = [issue for i in content_select]
        list_public_date = [i.find('h6', class_='pub-info').text.split('Published')[-1].strip() for i in
                            content_select]

        with requests.Session() as session:
            for i in range(len(content_select)):
                if len(self.c.execute("select id from papers where head_StrID=:value", {'value': list_head_StrID[i]}).fetchall()) != 0:
                    list_abstract.append('Exist in db.')
                    continue
                _r = session.get(''.join([journal_url, '/_api/v1/articles/', list_data_id[i], '/abstract']), headers=xhr_headers)
                if _r.status_code == 200:
                    list_abstract.append(_r.text[3:-4])
                else:
                    list_abstract.append('ERROR in get abstract: <Response [{}]>'.format(_r.status_code))

        _zip = zip(list_head_StrID, list_url, list_title, list_authors, list_note, list_abstract,
                   list_version, list_journal, list_volume, list_issue, list_public_date)
        for i, item in enumerate(_zip):
            items.append(item)

        return tabletitle, items

class ApsPRB(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_name = 'Phys. Rev. B'
        self.journal_note = ''

    def get_items(self):
        journal_url = self.journal_url
        journal_name = self.journal_name
        journal_note = self.journal_note
        xhr_headers = self.xhr_headers

        # get current issue url
        response = requests.get(journal_url + '/prb/recent')
        soup = BeautifulSoup(response.text, features='html.parser')
        current_issue_links = [i.find('a').attrs.get('href') for i in
                               soup.find('ul', class_='no-bullet').find_all('li')[:-1]]

        # get current issue
        items = []
        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'volume',
                      'issue', 'public_date']

        content_select = []
        list_volume = []
        list_issue = []
        for current_issue_link in current_issue_links:
            response = requests.get(journal_url + current_issue_link)
            soup = BeautifulSoup(response.text, "html.parser")

            vol_issue = soup.find('section', id='title').h2.text
            volume, issue = re.findall(r'\d+', vol_issue)

            content = soup.find('div', id='toc-content')
            content = content.find_all('div', class_='article panel article-result')
            content_select += content
            list_volume += [volume for i in content]
            list_issue += [issue for i in content]

        list_data_id = [i.attrs['data-id'] for i in content_select]
        list_head_StrID = [i.split('/')[-1] for i in list_data_id]
        list_url = [journal_url + i.a.attrs['href'] for i in content_select]
        list_title = [i.a.text for i in content_select]
        list_authors = [i.find('h6', class_='authors').text for i in content_select]
        list_note = [journal_note for i in content_select]
        list_abstract = []
        list_version = ['published' for i in content_select]
        list_journal = [journal_name for i in content_select]
        list_public_date = [i.find('h6', class_='pub-info').text.split('Published')[-1].strip() for i in content_select]

        with requests.Session() as session:
            for i in range(len(content_select)):
                if len(self.c.execute("select id from papers where head_StrID=:value", {'value': list_head_StrID[i]}).fetchall()) != 0:
                    list_abstract.append('Exist in db.')
                    continue
                _r = session.get(''.join([journal_url, '/_api/v1/articles/', list_data_id[i], '/abstract']), headers=xhr_headers)
                if _r.status_code == 200:
                    list_abstract.append(_r.text[3:-4])
                else:
                    list_abstract.append('ERROR in get abstract: <Response [{}]>'.format(_r.status_code))

        _zip = zip(list_head_StrID, list_url, list_title, list_authors, list_note, list_abstract,
                   list_version, list_journal, list_volume, list_issue, list_public_date)
        for i, item in enumerate(_zip):
            items.append(item)

        return tabletitle, items

class ApsPRResearch(PaperSpider, Aps):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        Aps.__init__(self)
        self.journal_name = 'Phys. Rev. Research'
        # self.journal_note = 'PRReearch:selected'

    def get_items(self):
        aps_subjects_label_concerned = self.aps_subjects_label_concerned
        journal_url = self.journal_url
        journal_name = self.journal_name
        journal_note = self.journal_note
        xhr_headers = self.xhr_headers

        # get current issue url
        response = requests.get(journal_url + '/prresearch')
        soup = BeautifulSoup(response.text, features='html.parser')
        current_issue_link = soup.find('a', id='current-issue-link').attrs.get('href')

        # get current issue
        items = []
        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'volume',
                      'issue', 'public_date']
        response = requests.get(journal_url + current_issue_link)
        soup = BeautifulSoup(response.text, "html.parser")

        vol_issue = soup.find('section', id='title').h2.text
        volume, issue = re.findall(r'\d+', vol_issue)

        content = soup.find('div', id='toc-content')
        content = content.find_all('div', class_='article-result')
        content_select = []
        for i in content:
            subjects_label = {j.text for j in i.find_all('a', class_='label')}
            if len(subjects_label & aps_subjects_label_concerned) > 0:
                content_select.append(i)

        list_data_id = [i.attrs['data-id'] for i in content_select]
        list_head_StrID = [i.split('/')[-1] for i in list_data_id]
        list_url = [journal_url + i.a.attrs['href'] for i in content_select]
        list_title = [i.a.text for i in content_select]
        list_authors = [i.find('h6', class_='authors').text for i in content_select]
        list_note = [journal_note for i in content_select]
        list_abstract = []
        list_version = ['published' for i in content_select]
        list_journal = [journal_name for i in content_select]
        list_volume = [volume for i in content_select]
        list_issue = [issue for i in content_select]
        list_public_date = [i.find('h6', class_='pub-info').text.split('Published')[-1].strip() for i in
                            content_select]

        with requests.Session() as session:
            for i in range(len(content_select)):
                if len(self.c.execute("select id from papers where head_StrID=:value", {'value': list_head_StrID[i]}).fetchall()) != 0:
                    list_abstract.append('Exist in db.')
                    continue
                _r = session.get(''.join([journal_url, '/_api/v1/articles/', list_data_id[i], '/abstract']), headers=xhr_headers)
                if _r.status_code == 200:
                    list_abstract.append(_r.text[3:-4])
                else:
                    list_abstract.append('ERROR in get abstract: <Response [{}]>'.format(_r.status_code))

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
        self.journal_url = r'https://www.nature.com/subjects/physical-sciences/nature'
        self.journal_note = 'All_Nat' # add to tag to receive all papers from Nature
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Physics(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Physics'
        self.journal_url = r'https://www.nature.com/subjects/physical-sciences/nphys'
        self.journal_note = 'All_Nat_Phys' # add to tag to receive all papers from Nat. Phys.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Materials(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Materials'
        self.journal_url = r'https://www.nature.com/subjects/physical-sciences/nmat'
        self.journal_note = 'All_Nat_Mater' # add to tag to receive all papers from Nat. Mater.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Nanotechnology(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Nanotechnology'
        self.journal_url = r'https://www.nature.com/subjects/physical-sciences/nnano'
        self.journal_note = 'All_Nat_Nanotechnol' # add to tag to receive all papers from Nat. Nanotechnol.
    def get_items(self):
        return get_items_nature(self.journal_name, self.journal_url, self.journal_note)

class Nature_Communications(PaperSpider):
    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Nature Communications'
        self.journal_url = r'https://www.nature.com/subjects/physical-sciences/ncomms'
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

