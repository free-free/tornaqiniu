#-*- coding:utf-8 -*-
from datetime import datetime
from .utils import *
from tornado import gen
from tornado import httpclient
from tornado.httpclient import AsyncHTTPClient
import copy


class Auth(object):

    def __init__(self, access_key, secret_key):
        assert access_key != None and access_key != "", "invalid access_key"
        assert secret_key != None and secret_key != "", "invalid secret_key"
        self.__access_key = access_key
        self.__secret_key = secret_key

    def upload_token(self, bucket, key=None, expires=3600, policys=None):
        assert bucket != None and bucket != "", "invalid bucket"
        all_policys = policys or {}
        if 'scope' not in all_policys:
            if key:
                all_policys['scope'] = bucket + ':' + key
            else:
                all_policys['scope'] = bucket
        if 'deadline' not in all_policys:
            all_policys['deadline'] = int(
                datetime.timestamp(datetime.now())) + expires
        json_policys = json_encode(all_policys)
        b64_encoded_policys = urlsafe_base64_encode(json_policys)
        sha1_sign = hmac_sha1(self.__secret_key, b64_encoded_policys)
        b64_encoded_sign = urlsafe_base64_encode(sha1_sign)
        upload_token = self.__access_key + ':' + \
            bytes_decode(b64_encoded_sign) + ':' + \
            bytes_decode(b64_encoded_policys)
        return upload_token

    def download_token(self, download_url, expires=3600):
        url = download_url
        if download_url.find("?") >= 0:
            url += "&e=" + \
                str(int(datetime.timestamp(datetime.now())) + expires)
        else:
            url += '?e=' + \
                str(int(datetime.timestamp(datetime.now())) + expires)
        download_token = self.access_token(url)
        return download_token

    def access_token(self, need_sign):
        sha1_sign = hmac_sha1(self.__secret_key, need_sign)
        b64_encoded_sign = urlsafe_base64_encode(sha1_sign)
        access_token = "{0}:{1}".format(
            self.__access_key, bytes_decode(b64_encoded_sign))
        return access_token

    def callback_verify_header(self, url_path, body=None):
        signing_str = url_path + "\n"
        if body:
            signing_str += body
        access_token = self.access_token(signing_str)
        return "QBox " + access_token


class Policy(object):
    _policy_map = {
        "scope": "scope",
        "deadline": "deadline",
        "insert_only": "insertOnly",
        "end_user": "endUser",
        "return_url": "returnUrl",
        "return_body": "returnBody",
        "callback_url": "callbackUrl",
        "callback_host": "callbackHost",
        "callback_body": "callbackBody",
        "callback_body_type": "callbackBodyType",
        "callback_fetch_key": "callbackFetchKey",
        "persistent_ops": "persistentOps",
        "persistent_notify_url": "persistentNotifyUrl",
        "persistent_pipeline": "persistentPipeline",
        "save_key": "saveKey",
        "fsize_min": "fsizeMin",
        "fsize_limit": "fsizeLimit",
        "detect_mime": "detectMime",
        "mime_limit": "mimeLimit",
        "delete_after_days": "deleteAfterDays",
    }
    _policys = {}

    def __init__(self, policys=None):
        assert isinstance(policys, (dict, type(None)))
        if isinstance(policys, dict):
            for policy_n, policy_v in policys.items():
                self._policys[policy_n] = policy_v

    def del_policy(self, policy_name):
        if policy_name in self._policys:
            del self._policys[policy_name]

    def __getattr__(self, policy_attr_name):
        policy_name = self._policy_map.get(policy_attr_name)
        if not policy_name:
            return None
        return self._policys.get(policy_name)

    def __setattr__(self, policy_attr_name, policy_value):
        policy_name = self._policy_map.get(policy_attr_name)
        if not policy_name:
            raise Exception("No such policy '%s'" % policy_attr_name)
        # when policy_value equal to None,that's means delete policy
        if policy_value == None:
            self.del_policy(policy_name)
        else:
            # The persistentOps and callbackUrl  have multi values,so it need
            # to process seperately
            if policy_name in ("persistentOps", "callbackUrl"):
                if not self._policys.get(policy_name):
                    self._policys[policy_name] = policy_value
                else:
                    self._policys[policy_name] += ';' + policy_value
            else:
                self._policys[policy_name] = policy_value

    def __setitem__(self, policy_name, policy_value):
        if policy_name not in self._policy_map.keys():
            raise Exception("No such  policy '%s'" % policy_name)
        self._policys[self._policy_map.get(policy_name)] = policy_value

    def __getitem__(self, policy_name):
        if policy_name in self._policy_map.keys():
            return self._policys.get(self._policy_map[policy_name])

    def __delitem__(self, policy_name):
        if policy_name in self._policy_map.keys():
            if self._policy_map[policy_name] in self._policys:
                del self._policys[self._policy_map[policy_name]]

    @property
    def policys(self):
        return self._policys

    def delete_all_policys(self):
        self._policys.clear()
