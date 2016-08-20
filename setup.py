#-*- coding:utf-8 -*-

from setuptools import setup,find_packages
import os
import re


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()

def find_version(f):
    file_content = read(f)
    try:
        return re.findall(r'^__version__ = "([^\'\"]+)"\r?$',
            file_content, re.M)[0]
    except IndexError:
        raise RuntimeError("Unable to determine version.")


setup(
    name="tornado_qiniu",
    version=find_version("tornado_qiniu/__init__.py"),
    author="HuangBiao",
    author_email="19941222hb@gmail.com",
    description="An asynchronous qiniu cloud storage sdk for tornado",
    long_description=read("README.rst"),
    license="MIT",
    url="https://github.com/free-free/tornaqiniu",
    packages=find_packages(),
    include_package_data=True,
    install_requires=['tornado', 'futures'],
    keywords=['tornado', 'qiniu', 'sdk'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ]
)
