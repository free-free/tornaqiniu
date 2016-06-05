#-*- coding:utf-8 -*-
from tornado import gen,httpclient
from tornado.httpclient import AsyncHTTPClient
import json
from .resource_manage import  QiniuResourceManager
from .resource_load import    QiniuResourceLoader
from .resource_process import QiniuResourceProcessor,_QiniuResourceOpsInterface
from .errors import EncodingError
from .utils import bytes_encode,bytes_decode,urlsafe_base64_encode,json_encode,json_decode,hmac_sha1
from .common import Auth
import base64
import hmac

class QiniuClient(object):
	def __init__(self,access_key,secret_key,download_host=None,bucket=None):
		self._auth=Auth(access_key,secret_key)
		self._resource_manager=QiniuResourceManager(bucket,self._auth)
		self._resource_loader=QiniuResourceLoader(bucket,self._auth)
		self._resource_processor=QiniuResourceProcessor(bucket,self._auth)
		self._bucket=bucket
		self._download_host=download_host
	def upload_token(self,bucket=None,key=None,expires=3600,policys=None):
		bucket=bucket or self._bucket
		assert bucket!=None and bucket!="","invalid bucket"
		if isinstance(policys,dict):
			self.add_policys(policys)
		return self._auth.upload_token(bucket,key,expires,self._resource_loader.policys)
	def add_policy(self,field,value):
		""" add one policy
		Args:
			field:policy name,
			value:policy value,
		Returns:
			None
		"""
		self._resource_loader.add_policy(field,value)
	def add_policys(self,policy_pairs):
		""" add multi policys
		Args:
			policy_pairs:dict type
		Returns:
			None
		"""
		self._resource_loader.add_policys(policy_pairs)
	def delete_policy(self,field):
		""" delete one policy
		Args:
			field:policy name
		Returns:
			None
		"""
		self._resource_loader.delete_policy(field)
	def delete_policys(self,fields):
		"""delete multi policys
		Args:
			fields:a tuple or list of policy name 
		Returns:
			None
		"""
		self._resource_loader.delete_policys(fields)
	def delete_all_policys(self):
		"""delete all policys
		"""
		self._resource_loader.delete_all_policys()
	def modify_policy(self,field,value):
		"""modify one policy,if policy not exists ,add it
		Args:
			field:policy name
			value:policy value
		Returns:
			None
		"""
		self._resource_loader.modify_policy(field,value)
	def update_policys(self,policy_pairs():
		"""update all policys
		Args:
			policy_pairs:dict type
		Returns:
			None
		"""
		self._resource_loader.get_flush_policys()
		self._add_policys(policy_pairs()
	@property
	def policys(self):
		"""get all policys
		Args:
			None
		Returns:
			all policys
		"""
		return self._resource_loader.get_policys()
