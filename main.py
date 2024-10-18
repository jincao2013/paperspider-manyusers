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
    config_path = '/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test/config.jin.json'
    config = Config(config_path)

    # arxiv = Arxiv(config)
    prl = ApsPRL(config)
    prx = ApsPRX(config)
    prb = ApsPRB(config)
    prresearch = ApsPRResearch(config)

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
    # prl.main(sendemail=False)
    # prx.main(sendemail=False)
    # prb.main(sendemail=False)
    # prresearch.main(sendemail=False)

    # tabletitle, items = arxiv.get_items()
    # tabletitle, items = prl.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()
    # tabletitle, items = nat_phys.get_items()

