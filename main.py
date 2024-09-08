import os
import sys
import time
import datetime
import random
from datetime import datetime, timedelta
import re
from paperspider.dbAPI import keyword_matching, Paper, Mailing_list

import numpy as np
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch
from paperspider.spider import Nature, Nature_Physics, Nature_Materials, Nature_Communications, Nature_Nanotechnology

# from .server import schedule

def generate_past_timestamps(num_days):
    now = time.time()
    seconds_per_day = 24 * 60 * 60
    return [now - i * seconds_per_day for i in range(num_days - 1, -1, -1)]



if __name__ == '__main__':
    # os.chdir('/Users/jincao/Downloads/temp')
    os.chdir('/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test')
    config_path = '/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test/config.test.json'
    config = Config(config_path)

    # arxiv = Arxiv(config)
    # prl = ApsPRL(config)
    # prx = ApsPRX(config)
    # prb = ApsPRB(config)
    # prresearch = ApsPRResearch(config)
    #
    # nature = Nature(config)
    # nat_phys = Nature_Physics(config)
    # nat_matr = Nature_Materials(config)
    # nat_nano = Nature_Nanotechnology(config)
    # nat_comm = Nature_Communications(config)

    # arxiv.main(sendemail=False)
    # nature.main(sendemail=False)
    # nat_phys.main(sendemail=False)
    # nat_matr.main(sendemail=False)
    # nat_nano.main(sendemail=False)
    # nat_comm.main(sendemail=False)
    # prl.main(sendemail=True)

    # tabletitle, items = arxiv.get_items()
    # tabletitle, items = prl.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()

    # with open('nat.html', 'w') as f:
    #     f.write(' '.join(nature.papers_html))
    #

    conn = config.conn
    # # head_StrID = 'test'
    # # paper = Paper(conn, head_StrID)
    # # paper.db_creat()
    # #
    # # paper.keywords = 'hall'
    # # paper.score_by_keywords = 11
    #

    # update_date = mail.update_date
    ''' for test, generate 50 fake mailing-list '''
    # past_50_days = generate_past_timestamps(50)[::-1]
    # subjects = ['arXiv', 'PRL', 'PRB', 'Nature', 'Ncomm']
    #
    # for i in range(50):
    #     subject_today = random.sample(subjects, 2)
    #     for j in subject_today:
    #         list_paper_idx = np.random.randint(35743 - 1000, 35743, size=40)
    #         list_paper_stridx = [i for i in map(str, list_paper_idx)]
    #         mail = Mailing_list(conn)
    #         mail.db_creat(j, list_paper_idx, list_paper_stridx, update_date=past_50_days[i])

    ''' code for get weekday from timestamp '''
    # # # time
    # current_time = 1721545214
    #
    # date_object = datetime.datetime.fromtimestamp(current_time)
    # day = date_object.strftime('%Y%m%d')
    # day_of_week = date_object.strftime('%w')
    #
    # days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    #
    #
    # local_time = time.localtime(current_time)
    # day_of_week = local_time.tm_year*1e4+local_time.tm_year*1e4+local_time.tm_mday
    # day_of_week = local_time.tm_wday
    # day_of_week_str = days[day_of_week]
    # print(day_of_week_str)
