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

import os
import sys
sys.path.append(os.environ.get('PYTHONPATH'))


import requests
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from collections import Counter
import os
import random

import smtplib
from email.header import Header
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def job1():
    with open('job1.txt', 'a') as f:
        while True:
            time.sleep(5)
            f.write('job1: tik')


def job2():
    with open('job2.txt', 'a') as f:
        while True:
            time.sleep(5)
            f.write('job2: tik')

def job_test():
    print('Job test')
    with open('job_test.txt', 'a') as f:
        f.write('job_test \n')
    f.close()


def job_printer():
    print("Hello World pid={}".format(os.getpid()))


def send_email(content):
    # receiver = 'caojin.phy@gmail.com' # receiver can be a list
    # receiver = '498612563@qq.com' # receiver can be a list
    content_head = """
     <p>
     Dear subscriber, </br>
     Here attached recent updated papers.  </br>
     Best,  </br>
     PaperSpider </br>
     </p>
     """
    title = 'TEST: Paper Spider'
    receiver = 'caojin.phy@gmail.com'

    # email of sender
    sender = 'paperspider@foxmail.com'
    user = 'paperspider@foxmail.com'
    password = 'btdzbzkwtgoibebg'
    # SMTP server of sender
    smtpserver = 'smtp.qq.com'
    smtp_port = 587

    message = MIMEMultipart('alternative')
    message['From'] = Header(sender, 'utf-8')
    message['To'] = Header(receiver, 'utf-8')
    message['Subject'] = Header(title, 'utf-8')

    message.attach(MIMEText(content_head, 'html', 'utf-8'))
    message.attach(MIMEText(content, 'html', 'utf-8'))

    smtp = smtplib.SMTP()
    # smtp = smtplib.SMTP_SSL()
    smtp.connect(smtpserver, smtp_port)  # default port 25 for smtp (unsafe)

    # smtp.ehlo(smtpserver)
    smtp.login(user, password)  # 登陆smtp服务器
    smtp.sendmail(sender, receiver, message.as_string())  # 发送邮件 ，这里有三个参数
    smtp.quit()


if __name__ == '__main__':
    pass
    # main()
    # time.sleep(1)

    from pytz import utc

    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
    from apscheduler.schedulers.blocking import BlockingScheduler

    # sched = BlockingScheduler()
    # sched = BackgroundScheduler()
    # sched.add_job(job_printer, 'interval', seconds=100)
    # sched.start()



    # print("father pid={}".format(os.getpid()))
    #
    # # jobstores = {
    # #     'mongo': MongoDBJobStore(),
    # #     'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    # # }
    # executors = {
    #     # 'default': ThreadPoolExecutor(10),
    #     'default': ProcessPoolExecutor(4),
    #     # 'processpool': ProcessPoolExecutor(5)
    # }
    # job_defaults = {
    #     'coalesce': True,
    #     'max_instances': 3
    # }
    # scheduler = BackgroundScheduler(executors=executors, job_default=job_defaults, timezone=utc)
    #
    #
    # scheduler.add_job(job_printer, 'interval', seconds=5, id='job1')
    # scheduler.add_job(job_printer, 'interval', seconds=6, id='job2')
    # scheduler.add_job(job_printer, 'interval', seconds=7, id='job3')
    # # scheduler.remove_job('job1')
    #
    # scheduler.start()
    # scheduler.remove_all_jobs()
    #
    # try:
    #     while True:
    #         time.sleep(100)
    #         print('sleep!')
    # except (KeyboardInterrupt, SystemExit):
    #     scheduler.remove_all_jobs()
    #     scheduler.shutdown()
    #     print('Exit the job !')

    with open('../test/paper.html') as f:
        content = f.read()
    f.close()
    send_email(content)