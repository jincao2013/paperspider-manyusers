import os
import sys
import time
import re
from paperspider.dbAPI import keyword_matching

import numpy as np
from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch
from paperspider.spider import Nature, Nature_Physics, Nature_Materials, Nature_Communications, Nature_Nanotechnology

# from .server import schedule


if __name__ == '__main__':
    # os.chdir('/Users/jincao/Downloads/temp')
    os.chdir('/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test')
    config_path = '/Users/jincao/Seafile/Coding/github/paperspider-manyusers/test/config.test.json'
    config = Config(config_path)

    arxiv = Arxiv(config)
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

