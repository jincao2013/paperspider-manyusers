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
# The paperspider-manyusers code is hosted on GitHub:
#
# https://github.com/jincao2013/paperspider-manyusers

import json
import os

import smtplib
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header


if __name__ == "__main__":

    # smtp_server = r'smtp.163.com'
    # smtp_port = 587 # 465 587
    # user = 'paperspider@163.com'
    # password = 'JWMHYJVVWDBUZIOW'

    smtp_server = r'smtp.qq.com'
    smtp_port = 587 # 465 587
    user = 'paperspider@foxmail.com'
    password = ''
    receiver = 'caojin.phy@gmail.com'
    subject = 'Python SMTP test'
    content_head = 'test2'
    content = r"""
This month,

<p>
While, it is straightforward to show in what limit classical mechanics follows
from quantum-mechanics, the path to show how quantum-mechanics may follow from
using probability distributions on classical trajectories is non-trivial. Daniel
Arovas explains the latest works showing progress in this problem.
</p>
Sincerely,

Organizers,
Journal Club for Condensed Matter Physics
"""

    message = MIMEMultipart('alternative')
    message['From'] = user
    message['To'] = receiver
    message['Subject'] = Header(subject, 'utf-8')
    message.attach(MIMEText(content_head + content, 'html', 'utf-8'))

    # smtp = smtplib.SMTP()
    smtp = smtplib.SMTP_SSL(smtp_server)
    smtp.connect(smtp_server, smtp_port)  # default port 25 for smtp (unsafe)

    smtp.login(user, password)
    smtp.sendmail(user, receiver, message.as_string())
    smtp.quit()
