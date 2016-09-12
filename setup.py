#!/usr/bin/env python

from distutils.core import setup

setup(name='dabmot',
      version='1.0.1',
      description='DAB MOT object assembly and decoding',
      author='Ben Poor',
      author_email='ben.poor@thisisglobal.com',
      url='https://github.com/GlobalRadio/python-dabmot',
      download_url='https://github.com/GlobalRadio/python-dabmot/tarball/1.0.1',
      packages=['mot'],
      package_dir = {'' : 'src'},
      keywords = ['dab', 'mot', 'radio']
     )
