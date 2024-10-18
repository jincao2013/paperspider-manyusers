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
import random
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch
from paperspider.spider import Nature, Nature_Physics, Nature_Materials, Nature_Communications, Nature_Nanotechnology

def schedule(config):
    """ start schedule """

    ''' init spider for each journal '''
    arxiv = Arxiv(config)
    prl = ApsPRL(config)
    prx = ApsPRX(config)
    prb = ApsPRB(config)
    prresearch = ApsPRResearch(config)
    nature = Nature(config)
    nat_phys = Nature_Physics(config)
    nat_matr = Nature_Materials(config)
    nat_nano = Nature_Nanotechnology(config)
    nat_comm = Nature_Communications(config)

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
    utc_hour = (6 - 8) % 24  # beijing_hour: 06:xx am
    minites = sorted(random.sample(range(0, 59), 5))
    scheduler.add_job(nature.main, id='nature', name='nature.main', trigger='cron', day_of_week='mon', hour=utc_hour, minute=minites[0])
    scheduler.add_job(nat_phys.main, id='nat_phys', name='nat_phys.main', trigger='cron', day_of_week='tue', hour=utc_hour, minute=minites[1])
    scheduler.add_job(nat_matr.main, id='nat_matr', name='nat_matr.main', trigger='cron', day_of_week='tue', hour=utc_hour, minute=minites[2])
    scheduler.add_job(nat_nano.main, id='nat_nano', name='nat_nano.main', trigger='cron', day_of_week='tue', hour=utc_hour, minute=minites[3])
    scheduler.add_job(nat_comm.main, id='nat_comm', name='nat_comm.main', trigger='cron', day_of_week='wed', hour=utc_hour, minute=minites[4])

    utc_hour = (7 - 8) % 24  # beijing_hour: 07:xx am
    minites = sorted(random.sample(range(0, 59), 4))
    scheduler.add_job(prl.main, id='prl', name='prl.main', trigger='cron', day_of_week='mon', hour=utc_hour, minute=minites[0])
    scheduler.add_job(prb.main, id='prb', name='prb.main', trigger='cron', month='*', day='1,6,11,16,21,26', hour=utc_hour, minute=minites[1])
    scheduler.add_job(prx.main, id='prx', name='prx.main', trigger='cron', month='*', day='5', hour=utc_hour, minute=minites[2])
    scheduler.add_job(prresearch.main, id='prresearch', name='prresearch.main', trigger='cron', month='*', day='1,15', hour=utc_hour, minute=minites[3])

    utc_hour = (9 - 8) % 24  # beijing_hour: 09:xx am
    scheduler.add_job(arxiv.main, id='arxiv', name='arxiv.main', trigger='cron', day='*', hour=utc_hour, minute=random.randint(0, 10))

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
