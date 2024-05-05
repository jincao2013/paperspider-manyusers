
import os
# import sys
import time
import random
# import sqlite3
# import logging
import re
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from paperspider.dbAPI import Paper

def keyword_matching(keywords, paragraph):
    # paragraph = """
    # The finite coupling between Weyl nodes due to residual disorder is investigated by magnetotransport studies in WTe2. The anisotropic scattering of quasiparticles is evidenced from classical and quantum transport measurements. A new theoretical approach using a real band structure is developed to calculate the dependence of the scattering anisotropy with the correlation length of the disorder. A comparison between theory and experiments reveals for the first time a short correlation length in WTe2 (ξ~nm). This result implies a significant coupling between Weyl nodes and other bands, so that inter-node scattering strongly reduces topologically non-trivial properties, such as the chiral anomaly.
    # """
    # keywords = ['weyl', 'WTe2', 'test']
    relative = float(len(set(re.search(k, paragraph, re.I | re.M) for k in keywords) - {None}))
    return relative

if __name__ == "__main__":
    # wdir = r''
    # os.chdir(wdir)

    journal_name = 'Nature Physics'
    journal_url = r'https://www.nature.com/subjects/physical-sciences/nphys'

    paragraph = """
    The finite coupling between Weyl nodes due to residual disorder is investigated by magnetotransport studies in WTe2. The anisotropic scattering of quasiparticles is evidenced from classical and quantum transport measurements. A new theoretical approach using a real band structure is developed to calculate the dependence of the scattering anisotropy with the correlation length of the disorder. A comparison between theory and experiments reveals for the first time a short correlation length in WTe2 (ξ~nm). This result implies a significant coupling between Weyl nodes and other bands, so that inter-node scattering strongly reduces topologically non-trivial properties, such as the chiral anomaly.
    """
    keywords = ['weyl', 'WTe2', 'test', 'VEST']
    set(re.search(k, paragraph, re.I | re.M) for k in keywords)
