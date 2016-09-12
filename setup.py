#!/usr/bin/env python

from distutils.core import setup

setup(name='dabmot',
      version='1.0.0',
      description='DAB MOT object assembly and decoding',
      author='Ben Poor',
      author_email='ben.poor@thisisglobal.com',
      packages=['mot'],
      package_dir = {'' : 'src'}
      keywords = ['dab', 'mot', 'radio']
     )
