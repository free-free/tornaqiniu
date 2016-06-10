#-*- coding:utf-8 -*-
from tornado import gen,httpclient
from tornado.httpclient import AsyncHTTPClient
import json
from .resource import *
from .errors import EncodingError
from .bucket import Bucket
from .utils import bytes_encode,bytes_decode,urlsafe_base64_encode,json_encode,json_decode,hmac_sha1
from .common import Auth
import base64
import hmac

class QiniuClient(object):
	def __init__(self,access_key,secret_key,download_host=None,bucket=None,bucket_acp=0):
		self._auth=Auth(access_key,secret_key)
		self._bucket=bucket
		self._download_host=download_host
		self._bucket_acp=bucket_acp
	def bucket(self,bucket_name,host=None,bucket_acp=0):
		return Bucket(host or self._download_host,self._auth,bucket_name,bucket_acp)
