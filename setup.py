from setuptools import setup

# for release package: python setup.py sdist
setup(
    name='paperspider-manyusers',
    version='1.0.0',
    packages=['paperspider', 'test'],
    include_package_data=True,
    url='',
    license='',
    author='jincao',
    author_email='caojin.phy@gmail.com',
    description=''
)

'''
  To release package, make sure:
  1. server.py, foreground=False 
'''
