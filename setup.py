from setuptools import setup
from paperspider.version import __version__, __author__, __email__


packages_paperspider = [
    'paperspider',
]

setup(
    name='paperspider',
    version=__version__,
    include_package_data=True,
    packages=packages_paperspider,
    # packages=setuptools.find_packages(),
    url='https://github.com/jincao2013/paperspider-manyusers',
    license='Apache License, Version 2.0',
    author=__author__,
    author_email=__email__,
    description='This is the paperspider module.',
    python_requires='>=3.6',
    install_requires=['numpy', 'requests', 'pytz', 'apscheduler', 'sqlite3', 'bs4'],
)
'''
  To release package, make sure:
  1. server.py, foreground=False
'''