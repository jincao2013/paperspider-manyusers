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

import os
import sys
import time
import random
import sqlite3
import logging
import re

import requests
from bs4 import BeautifulSoup

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

from paperspider.dbAPI import Paper


def echo_time(int_time=None):
    if int_time == None:
        _int_time = time.time()
    else:
        _int_time = int_time
    return time.strftime("%b.%d,%Y; %a; %H:%M:%S", time.localtime(_int_time))


'''
  * sender
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
  * Inspect papers daily
'''
class PaperSpider(object):

    def __init__(self, config):
        self.config = config
        self.logger = config.logger
        self.conn = config.conn
        self.c = self.conn.cursor()
        self.sender = config.sender

        self.journal_url = None
        self.journal_name = None
        # self.interval_update = 24 # hours

        self.user_names = [i.name for i in config.users]
        self.user_emails = [i.email for i in config.users]
        self.num_users = config.num_users

        self.num_items = 0
        self.papers = []   # []
        self.papers_html = []
        # self.userinfos = []  # [(username, email), ...]
        self.preference_matrix = []  # [num_users * num_items]
        self.email_count = []

    def get_html(self):
        response = requests.get(self.journal_url)
        # print(response.status_code)
        while response.status_code == 403:
            time.sleep(500 + random.uniform(0, 500))
            response = requests.get(self.journal_url)
            # print(response.status_code)
        # print(response.status_code)
        if response.status_code == 200:
            return response.text
        return None

    def get_items(self):
        '''
          * tabletitle = ['head_StrID', ...]
            items = [item1, ...]
        ''' #
        tabletitle, items = [], []
        raise NotImplementedError

    def main(self, sendemail=True):
        self.num_items = 0
        self.papers = []  # []
        self.papers_html = []
        self.preference_matrix = []  # [num_users * num_items]
        self.email_count = []

        tabletitle, items = self.get_items()
        for i, item in enumerate(items):
            head_StrID = item[0]
            # check duplication
            if len(self.c.execute("select id from papers where head_StrID='{}'".format(head_StrID)).fetchall()) != 0:
                continue
            # if not found in DB:
            self.papers.append(Paper(self.conn, head_StrID))
            self.papers[self.num_items].db_creat()
            for name, value in zip(tabletitle, item):
                self.papers[self.num_items].__setattr__(name, value)
            self.num_items += 1

        # print(items)
        # print(self.num_items)
        if self.num_items == 0:
            self.logger.info('No update today.')
            return
        self.logger.info('{} new papers'.format(self.num_items))

        [i.pair_tags() for i in self.papers]
        self.preference_matrix = [i.compute_all_users_preferences(self.user_names) for i in self.papers]  # [num_items * num_users]

        # self.userinfos = preference[0][0]
        # self.num_users = len(self.userinfos)
        # self.preference_matrix = [i[1] for i in preferences] # [num_items * num_users]
        self.preference_matrix = [[row[i] for row in self.preference_matrix] for i in range(self.num_users)]  # [num_users * num_items]
        # self.papers = papers
        self.papers_html = [i.get_html() for i in self.papers]

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
            for j in range(self.num_items):
                if self.preference_matrix[i][j] > 0.5:
                    self.email_count[i] += 1
                    contents[i] += self.papers_html[j]
            contents[i] = """
            <div style="width: 70%">
                <ol>
            """ + contents[i] + """
                </ol>
            </div>
            """
        for i in range(self.num_users):
            if self.email_count[i] > 0:
                self.logger.info('email {} new articals to {}'.format(self.email_count[i], self.user_names[i]))
                # self.send_email(self.user_emails[i], contents[i])
                self.sender.send_email(self.user_emails[i], title, content_head, contents[i])
                time.sleep(random.random() * 60 * 1)
            else:
                self.logger.info('email no articals to {}'.format(self.user_names[i]))


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


class Arxiv(PaperSpider):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_name = 'Arxiv:cond-mat'
        # self.journal_url = 'https://arxiv.org/list/cond-mat.mes-hall/new?show=10'
        self.journal_url = 'https://arxiv.org/list/cond-mat.mes-hall/new'
        self.time_update = 24 # hours

    def get_items(self):
        # debug
        # html = open('./test/arxiv_tmp.html').read()
        # soup = BeautifulSoup(html, features='html.parser')

        soup = BeautifulSoup(self.get_html(), features='html.parser')
        content = soup.find('div', id='dlpage')
        # content = soup.dl
        # content = soup.find_all('dl')[1]
        date = soup.find('div', class_='list-dateline').text

        list_ids = content.find_all('a', title='Abstract')
        list_title = content.find_all('div', class_='list-title mathjax')
        list_authors = content.find_all('div', class_='list-authors')
        list_subjects = content.find_all('div', class_='list-subjects')
        list_subject_split = []
        for subjects in list_subjects:
            subjects = subjects.text.split(': ')[1]
            subjects = subjects.replace('\n\n', '')
            subjects = subjects.replace('\n', '')
            subject_split = subjects.split('; ')
            list_subject_split.append(subject_split)
        list_note = [str(i) for i in list_subject_split]

        list_abstract = content.find_all('p', class_='mathjax')
        list_abstract = [i.text.replace('\n', ' ') for i in list_abstract]

        items = []
        for i, item in enumerate(zip(list_ids, list_title, list_authors, list_note, list_abstract)):
            items.append([item[0].text, r'https://arxiv.org'+item[0].attrs['href'], item[1].text, item[2].text, item[3], item[4], 'preprint', 'arxiv', date])
        tabletitle = ['head_StrID', 'url', 'title', 'authors', 'note', 'abstract', 'version', 'journal', 'public_date']

        # paper = pd.DataFrame(columns=name, data=items)
        # # paper.to_csv('/home/zzh/Code/Spider/paperspider/arxiv/daily/'+time.strftime("%Y-%m-%d")+'_'+str(len(items))+'.csv')
        # paper.to_csv('arxivtodate.csv')

        return tabletitle, items


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

        # with requests.Session() as session:
        #     list_r_abstract = [
        #         session.get(''.join([journal_url, '/_api/v1/articles/', _data_id, '/abstract']), headers=xhr_headers)
        #         for _data_id in list_data_id
        #     ]
        #     list_abstract = [i.text[3:-4] for i in list_r_abstract]

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


class TempSpider(PaperSpider):

    def __init__(self, config):
        PaperSpider.__init__(self, config)
        self.journal_url = 'https://journals.aps.org'

    def get_items(self):
        '''
          * tabletitle = ['head_StrID', ...]
            items = [item1, ...]
        ''' #
        tabletitle, items = [], []
        raise NotImplementedError


# class A(object):
#
#     def __init__(self):
#         self.x = 10
#
#     def __getattr__(self, item):
#         return item
#
# a = A()

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

