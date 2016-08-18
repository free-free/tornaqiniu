#-*- coding:utf-8 -*-
from tornado import gen, httpclient
from tornado.httpclient import AsyncHTTPClient
import json
from .resource import *
from .errors import EncodingError
from .bucket import Bucket
from .utils import bytes_encode, bytes_decode, urlsafe_base64_encode, json_encode, json_decode, hmac_sha1
from .common import Auth
import base64
import hmac


class QiniuClient(object):

    def __init__(self, access_key, secret_key, host=None):
        self._auth = Auth(access_key, secret_key)
        self.__host = host

    def bucket(self, bucket_name, bucket_acp=0, host=None):
        return Bucket(host or self.__host, self._auth, bucket_name, bucket_acp)
