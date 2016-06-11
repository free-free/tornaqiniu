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
	def update_policys(self,policy_pairs):
		"""update all policys
		Args:
			policy_pairs:dict type
		Returns:
			None
		"""
		self._resource_loader.get_flush_policys()
		self._add_policys(policy_pairs())
	@property
	def policys(self):
		"""get all policys
		Args:
			None
		Returns:
			all policys
		"""
		return self._resource_loader.get_policys()
	def private_url(self,key,expires=3600,host=None):
		"""create private resource url
		Args:
			key:resource key
			expires:url expires time
			host:resource host
		Returns:
			resource private url
		"""
		return self._resource_loader.private_url(key,expires,host or self._download_host)
	def private_urls(self,keys,expires=3600,host=None,key_name=None):
		"""create private resource url for multi keys
		Args:
			keys:resource key list or tuple
			expires:url expires time
			host:resource host
			key_name:when inside key list,there is dict type value,you must point out key in this dict,for example:
				key_list=[{"key_name":"dejiode.jog","other":"dede"},{..},{..}]
		Returns:
			a list of resource private url
		"""
		return self._resource_loader.private_urls(keys,expires,host or self._download_host,key_name)
	def public_url(self,key,host=None):
		"""create public resource url
		Args:
			key:resource key
			host:resource host
		Returns:
			resource public url
		"""
		return self._resource_loader.public_url(key,host or self._download_host)
	def public_urls(self,keys,host=None,key_name=None):
		"""create url for multi keys
		Args:
			almost same with 'private_urls(**)' except 'expires'
		Returns:
			a list of resource public url
		"""
		return self._resource_loader.public_urls(keys,host or self._download_host,key_name) 			
	@gen.coroutine
	def stat(self,key,bucket=None):
		"""get resource detail information
		Args:
			key:resource key
			bucket:bucket name,if bucket name is None,self._bucket will replace it
		Returns:
			a dict for resource information
		"""
		response=yield self._resource_manager.stat(key,bucket or self._bucket)
		return response
	@gen.coroutine
	def move(self,s_bucket,s_key,d_bucket,d_key):
		""" move resource to another bucket,it's a tornado coroutine
		Args:
			s_bucket:src bucket name
			s_key:src key name
			d_bucket:destination bucket name
			d_key:destination key name
		Returns:
		
		"""
		response=yield self._resource_manager.move(s_bucket,s_key,d_bucket,d_key)
		return response
	@gen.coroutine
	def copy(self,s_bucket,s_key,d_bucket,d_key):
		""" copy resource to another bucket,it's a tornaod coroutine
		Args:
			almost same with 'move(**)'
		Returns:
			None
		"""
		response=yield self._resource_manager.copy(s_bucket,s_key,d_bucket,d_key)
		return response
	@gen.coroutine
	def delete(self,key,bucket=None):
		"""delete a resource
		Args:
			key:resource key name
			bucket:bucket name,if bucket is None,self._bucket will replace it
		Returns
			None
		"""
		response=yield self._resource_manager.delete(key,bucket or self._bucket)
		return response
	@gen.coroutine
	def list(self,bucket=None,limit=1000,prefix="",delimiter="",marker=""):
		"""list  resource detail information that meet requirements
		Args:
			refer to qiniu document
		Returns:
			a list of resource information
		"""
		response=yield self._resource_manager.list(bucket or self._bucket,limit,prefix,delimiter,marker)
		return response
	@gen.coroutine
	def fecth_store(self,fetch_url,key=None,bucket=None):
		"""fecth resource of 'fecth_url' ,then save it to 'bucket'
		Args:
			fetch_url:fetch url
			key:resource saving key name
			bucket:resource saving bucket name
		Returns:
			None
		"""
		response=yield self._resource_manager.fetch_store(fetch_url,key,bucket or  self._bucket)
		return response
	@gen.coroutine
	def bacth(self,*opers):
		""" execute multi resource management operations
		Args:
			*opers:opertions
		Returns:
			None
		"""
		response=yield self._resource_manager.bacth(*opers)
		return response
	@gen.coroutine
	def prefecth(self,key,bucket=None):
		response=yield self._resource_manager.prefetch(key,bucket or self._bucket)
		return response
