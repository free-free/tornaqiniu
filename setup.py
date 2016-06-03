#-*- coding:utf-8 -*-

from setuptools import setup,find_packages

setup(
	name="tornaqiniu",
	version="1.0",
	author="HuangBiao",
	author_email="19941222hb@gmail.com",
	description="An asynchronous qiniu cloud storage client for tornado",
	license="MIT",
	packages=find_packages(),
	include_package_data=True
)
