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

__date__ = "Sep. 8, 2024"

import os
import sys
from paperspider.config import Config
from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

def get_mailing_list():
    conn = config.conn
    cursor = conn.cursor()

    def_weeks = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    _mailing_list = cursor.execute("select id, subject, skimmed, starred, update_date_yymmdd, update_date_weekday from mailing_list").fetchall()
    mailing_list = []
    for row in _mailing_list:
        _dict = {
            'id': row[0],
            'subject': row[1],
            'skimmed': row[2],
            'starred': row[3],
            'update_date_yymmdd': row[4],
            'update_date_weekday': def_weeks[int(row[5])],
        }
        mailing_list.append(_dict)
    return mailing_list

# def get_mail_details(mail_id):
#     return str(mail_id)

def get_mail_details(mail_id):
    conn = config.conn
    cursor = conn.cursor()

    def_weeks = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    thismail = cursor.execute("select subject, update_date, update_date_weekday, list_paper_idx from mailing_list where id={}".format(mail_id)).fetchone()
    subject = thismail[0]
    update_date = thismail[1]
    update_date_weekday = def_weeks[thismail[2]]
    list_paper_idx = [i for i in map(int, thismail[3].split(';'))]

    # Create the parameterized query
    placeholders = ','.join('?' * len(list_paper_idx))
    query = f"select title, journal, authors, public_date, year from papers where id in ({placeholders})"
    papers_list = cursor.execute(query, list_paper_idx).fetchall()

    # email info
    email_info = {
        'subject': subject,
        'update_date': update_date,
        'update_date_weekday': update_date_weekday,
        'num_papers': len(list_paper_idx),
    }
    # Map results to a list of dictionaries
    papers = []
    for row in papers_list:
        paper_dict = {
            'title': row[0],
            'journal': row[1],
            'authors': row[2],
            'public_date': row[3],
            'year': row[4]
        }
        papers.append(paper_dict)

    return email_info, papers


@app.route('/')
def index():
    mailing_list = get_mailing_list()
    return render_template('index.html', mailing_list=mailing_list)

@app.route('/mail/<int:mail_id>')
def mail(mail_id):
    email_info, papers = get_mail_details(mail_id)
    return render_template('mail.html', email_info=email_info, papers=papers)


if __name__ == '__main__':
    # usage = 'usage: python3 app.py /etc/paperspider/config.json'
    # try:
    #     config_path = sys.argv[1]
    # except IndexError:
    #     print(usage)
    #     sys.exit(1)
    # config = Config(config_path, enable_log=False)
    # app.run(debug=True)

    ''' debug '''
    os.chdir('/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test')
    config_path = '/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test/config.test.json'
    config = Config(config_path, enable_log=False)
    app.run(debug=True)

    # conn = config.conn
    # cursor = conn.cursor()

