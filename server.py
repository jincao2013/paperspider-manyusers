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
import sys
import time

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch


def schedule(config):
    """ start schedule """

    ''' init spider for each journal '''
    arxiv = Arxiv(config)
    prl = ApsPRL(config)
    prx = ApsPRX(config)
    prb = ApsPRB(config)
    prresearch = ApsPRResearch(config)

    ''' init scheduler '''
    executors = {
        'default': ThreadPoolExecutor(10),
        # 'processpool': ProcessPoolExecutor(5)
    }
    job_defaults = {
        'coalesce': True,
        # 'max_instances': 3,
    }
    scheduler = BackgroundScheduler(executors=executors, job_default=job_defaults, timezone=utc)

    ''' assign spider jobs to schedule '''
    utc_hour = (9 - 8) % 24  # beijing_hour: 09:xx am
    scheduler.add_job(arxiv.main, id='arxiv', name='arxiv.main', trigger='cron', day='*', hour=utc_hour, minute=10)

    utc_hour = (7 - 8) % 24  # beijing_hour: 07:xx am
    scheduler.add_job(prl.main, id='prl', name='prl.main', trigger='cron', day_of_week='mon,thu', hour=utc_hour, minute=0)
    scheduler.add_job(prx.main, id='prx', name='prx.main', trigger='cron', month='*', day='5', hour=utc_hour, minute=15)
    scheduler.add_job(prb.main, id='prb', name='prb.main', trigger='cron', day_of_week='mon', hour=utc_hour, minute=30)
    scheduler.add_job(prresearch.main, id='prresearch', name='prresearch.main', trigger='cron', month='*', day='25', hour=utc_hour, minute=45)

    # scheduler.add_job(arxiv.main, id='arxiv_test')

    ''' start to run jobs in schedule '''
    scheduler.start()

    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.remove_all_jobs()
        scheduler.shutdown()


def main():
    usage = 'usage: python3 server.py /etc/paperspider/config.json'
    try:
        config_path = sys.argv[1]
    except IndexError:
        print(usage)
        sys.exit(1)

    config = Config(config_path)
    schedule(config)


if __name__ == '__main__':
    main()

    '''
      Debug
    '''
    # config_path = './test/config.test.json'
    # config = Config(config_path)l


    # config = Config()
    # arxiv = Arxiv(config)
    # prl = Aps(config)
    # arxiv.main()
    # prl.main()

    # c = config.c
    # u = r'\xf6'
    # c.execute("insert into papers (id, head_added_date, head_StrID, title) values (?,?,?,?)", (52, int(time.time()), u, " green's function"))
    # config.conn.commit()
