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
import json
import time
import sqlite3
import logging
from paperspider.dbAPI import User, Tag
from paperspider.spider import Sender


class Config(object):

    def __init__(self, config_path='/etc/paperspider/config.json'):
        self.config_path = config_path
        self.config = self.load_config_json()

        self.wdir = os.getcwd()
        # self.db_path = os.path.join(self.wdir, 'paperspider-db/sciDB.sqlite')
        self.db_path = self.config['database']['path']
        self.log_path = self.config['log']['path']
        self.loglevel = self.config['log']['loglevel']

        self.logger = self.set_logger()

        self.init_db()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.c = self.conn.cursor()

        self.sender = Sender(
            user=self.config['sender']['email'],
            password=self.config['sender']['password'],
            smtp_server=self.config['sender']['smtp_server'],
            smtp_port=self.config['sender']['smtp_port'],
        )
        self.tags = []
        self.users = []
        self.set_tags()
        self.set_users()

        # system
        self.start_time = time.asctime()
        self.num_get_papers = 0
        self.interval_update_paper = 24
        self.interval_update_preference_DB = 24*30

        # database
        self.num_tot_papers = 0
        self.num_users = len(self.users)
        self.num_tags = len(self.tags)
        self.num_subjects = 0

        self.logger.debug('config complete')

    def load_config_json(self):
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        return config

    def init_db(self):
        db_init_path = os.path.join(self.wdir, 'paperspider/sciDB.init.sql')
        if not os.path.exists(self.db_path):
            self.logger.debug('Database not found')
            os.system('sqlite3 {} < {}'.format(self.db_path, db_init_path))
            self.logger.debug('New Database created at {}'.format(self.db_path))

    def set_logger(self):
        logger = logging.getLogger()
        logger.setLevel(self.loglevel)

        # console Handler
        consoleHandler = logging.StreamHandler()
        consoleHandler.setLevel(self.loglevel)

        # file Handler
        fileHandler = logging.FileHandler(self.log_path, mode='w', encoding='UTF-8')
        fileHandler.setLevel(self.loglevel)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        consoleHandler.setFormatter(formatter)
        fileHandler.setFormatter(formatter)

        # add to Logger
        logger.addHandler(consoleHandler)
        logger.addHandler(fileHandler)

        return logger

    def set_tags(self):
        # '''
        #   Build-in tags
        # '''
        # _tag = Tag(self.conn, 'APS:selected')
        # _tag.db_creat()
        # _tag.dict = ['PRL:Cond-mat', 'PRX:selected']
        # self.tags.append(_tag)
        #
        # _tag = Tag(self.conn, 'Tag:topo')
        # _tag.db_creat()
        # _tag.dict = ['topological', 'weyl', 'semimetal']
        # self.tags.append(_tag)
        #
        # _tag = Tag(self.conn, 'Tag:twist')
        # _tag.db_creat()
        # _tag.dict = ['twisted graphene', 'twist graphene', 'magic angle']
        # self.tags.append(_tag)
        #
        # _tag = Tag(self.conn, 'Tag:response')
        # _tag.db_creat()
        # _tag.dict = ['green function', 'linear response',
        #              'nonlinear response', 'nonlinear optical',
        #              'Circular Photogalvanic', 'CPGE', 'shift current']
        # self.tags.append(_tag)

        tags = self.config['tags']
        for i in tags:
            _tag = Tag(self.conn, i['name'])
            _tag.db_creat()
            _tag.dict = i['dict']
            self.tags.append(_tag)

    def set_users(self):
        # _user = User(self.conn, 'jincao')
        # _user.db_creat()
        # _user.email = 'caojin.phy@gmail.com'
        # _tags = ['APS:selected', 'Tag:topo', 'Tag:twist', 'Tag:response']
        # _user.pair_tags(_tags, mode='update')
        # self.users.append(_user)

        # _user = User(self.conn, 'llp')
        # _user.db_creat()
        # _user.email = 'liuliping@bit.edu.cn'
        # _user.pair_tags(['topo'], mode='update')
        # self.users.append(_user)

        users = self.config['receiver']
        for i in users:
            _user = User(self.conn, i['name'])
            _user.db_creat()
            _user.email = i['email']
            _tags = i['tags']
            _user.pair_tags(_tags, mode='update')
            self.users.append(_user)
