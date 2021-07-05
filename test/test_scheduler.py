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
import time

from apscheduler.schedulers.background import BackgroundScheduler


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

if __name__ == '__main__':
    pass