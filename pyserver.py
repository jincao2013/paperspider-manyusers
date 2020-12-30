#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Jin Cao'
__copyright__ = "Copyright 2020, Quantum Functional Materials Design and Application Laboratory"
__version__ = "0.1"
__maintainer__ = "Jin Cao"
__email__ = "caojin.phy@gmail.com"
__date__ = "Feb. 7, 2020"

import os
import sys
import time
# import json
# import atexit
# import sqlite3

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
# from apscheduler.schedulers.blocking import BlockingScheduler

from paperspider.daemon import Daemon
from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch


def test_job(job_id):
    print('debug job pid={}'.format(os.getpid()))
    with open('job.out', 'a') as f:
        f.write('{}: job_id={} running at pid={} \n'.format(time.asctime(), job_id, os.getpid()))
    f.close()


def test_run(config=None):
    scheduler = BackgroundScheduler()

    scheduler.add_job(test_job, kwargs={'job_id': '1'}, trigger='interval', seconds=5, id='1')
    print('[INFO] job 1 added')
    scheduler.add_job(test_job, kwargs={'job_id': '2'}, trigger='interval', seconds=8, id='2')
    print('[INFO] job 2 added')
    scheduler.add_job(test_job, kwargs={'job_id': '3'}, trigger='interval', seconds=11, id='3')
    print('[INFO] job 3 added')
    scheduler.start()
    print('[INFO] scheduler start')

    try:
        while True:
            print('[INFO] scheduler is sleeping ...')
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print('[INFO] remove all jobs ...')
        scheduler.remove_all_jobs()
        print('[INFO] scheduler shutdown ...')
        scheduler.shutdown()
        print('[INFO] Exit.')


def initialization(config):
    conn = config.conn


def schedule(config):

    arxiv = Arxiv(config)
    prl = ApsPRL(config)
    prx = ApsPRX(config)
    prb = ApsPRB(config)
    prresearch = ApsPRResearch(config)

    '''
      * scheduler
    '''
    executors = {
        'default': ThreadPoolExecutor(10),
        # 'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': True,
        # 'max_instances': 3,
    }
    scheduler = BackgroundScheduler(executors=executors, job_default=job_defaults, timezone=utc)

    utc_hour = (6 - 8) % 24  # beijing_hour: 6
    scheduler.add_job(arxiv.main, id='arxiv', name='arxiv.main', trigger='cron', day='*', hour=utc_hour, minute=0)

    utc_hour = (7 - 8) % 24  # beijing_hour: 7
    scheduler.add_job(prl.main, id='prl', name='prl.main', trigger='cron', day_of_week='mon,fri', hour=utc_hour, minute=0)
    scheduler.add_job(prx.main, id='prx', name='prx.main', trigger='cron', month='*', day='20', hour=utc_hour, minute=15)
    scheduler.add_job(prb.main, id='prb', name='prb.main', trigger='cron', day_of_week='sun', hour=utc_hour, minute=30)
    scheduler.add_job(prresearch.main, id='prresearch', name='prresearch.main', trigger='cron', month='*', day='25', hour=utc_hour, minute=45)

    # scheduler.add_job(arxiv.main, id='arxiv_test')

    scheduler.start()

    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.remove_all_jobs()
        scheduler.shutdown()


class DaemonMaster(Daemon):
    def __init__(self, *args, **kwargs):
        super(DaemonMaster, self).__init__(*args, **kwargs)

    def run(self):
        config = Config()
        initialization(config)
        schedule(config)

    # def run(self):
    #     # used for debug
    #     test_run()


def main(foreground=False):
    if not foreground:
        arg = sys.argv[1]
        if arg in ('start', 'stop', 'restart'):
            # d = DaemonMaster('spiderd.pid', verbose=1, stdout='./debug.out', stderr='./debug.out') # used for debug
            d = DaemonMaster('spiderd.pid', verbose=1)
            getattr(d, arg)()  # i.e. d.start()
    else:
        # Foreground debug
        d = DaemonMaster('spiderd.pid', verbose=1, stdout='./debug.out', stderr='./debug.out')
        d.run()


if __name__ == '__main__':
    main(foreground=False)


    # config = Config()
    # initialization(config)
    # arxiv = Arxiv(config)
    # prl = Aps(config)
    # arxiv.main()
    # prl.main()

    # c = config.c
    # u = r'\xf6'
    # c.execute("insert into papers (id, head_added_date, head_StrID, title) values (?,?,?,?)", (52, int(time.time()), u, " green's function"))
    # config.conn.commit()
