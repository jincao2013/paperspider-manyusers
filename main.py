# import os
import sys
import time

from pytz import utc
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor

from paperspider.config import Config
from paperspider.spider import Arxiv, ApsPRL, ApsPRX, ApsPRB, ApsPRResearch

# from .server import schedule


if __name__ == '__main__':

    config_path = './test/config.test.json'
    config = Config(config_path)

    arxiv = Arxiv(config)
    prl = ApsPRL(config)
    prx = ApsPRX(config)
    prb = ApsPRB(config)
    prresearch = ApsPRResearch(config)

    # arxiv.main(sendemail=False)

