#-*- coding:utf-8 -*-
import functools
from tornado import gen
from .common import Policy
from .resource import Resource,QiniuResourceLoader,QiniuResourceManager,QiniuResourceProcessor
from .interface import QiniuInterface
class Bucket(object):
	def __init__(self,host,auth,bucket_name,bucket_acp=0):
		r"""
		Args:
			auth:qiniu authentication object
			bucket_name:bucket name
			bucket_acp: bucket access property
				0--->public bucket
				1--->private bucket
		"""
		self.__host=host
		self.__auth=auth
		self.__bucket_name=bucket_name
		self.__bucket_acp=bucket_acp
		self.__res_loader=QiniuResourceLoader(self.__auth)
		self.__res_manager=QiniuResourceManager(self.__auth)
		self.__res_processor=QiniuResourceProcessor(self.__auth)
		self.__policy=Policy()
	@property
	def acp(self):
		return self.__bucket_acp
	@property
	def bucket_name(self):
		return self.__bucket_name
	@property
	def auth(self):
		return self.__auth
	@property
	def resources(self):
		return self.__resources
	def res(self,*res_key):
		return Resource(self,*res_key)
	def upload_token(self,key=None,bucket=None,expires=3600,policys=None):
		bucket=bucket or self.__bucket_name
		assert bucket!=None and bucket!="","invalid bucket"
		if isinstance(policys,Policy):
			all_policys=policys.policys
		elif isinstance(policys,dict):
			all_policys=policys
		else:
			all_policys=self.__policy.policys
		return self.__auth.upload_token(bucket,key,expires,all_policys)
	def private_url(self,key,expires=3600,host=None):
		"""create private resource url
		Args:
			key:resource key
			expires:url expires time
			host:resource host
		Returns:
			resource private url
		"""
		return self.__res_loader.private_url(key,expires,host or self.__host)
	def public_url(self,key,host=None):
		"""
		Args:
			key:resource key name
		Returns:
			resource public url
		"""
		return self.__res_loader.public_url(key,host or self.__host)
	@gen.coroutine
	def stat(self,key,bucket=None):
		"""get resource detail information
		Args:
			key:resource key
			bucket:bucket name,if bucket name is None,self._bucket will replace it
		Returns:
			a dict for resource information
		"""
		response=yield self.__res_manager.stat(key,bucket or self._bucket)
		return response
	@gen.coroutine
	def move(self,s_key,s_bucket,d_key,d_bucket):
		""" move resource to another bucket,it's a tornado coroutine
		Args:
			s_bucket:src bucket name
			s_key:src key name
			d_bucket:destination bucket name
			d_key:destination key name
		Returns:
		
		"""
		response=yield self.__res_manager.move(s_key,s_bucket,d_key,d_bucket)
		return response
	@gen.coroutine
	def copy(self,s_key,s_bucket,d_key,d_bucket):
		""" copy resource to another bucket,it's a tornaod coroutine
		Args:
			almost same with 'move(**)'
		Returns:
			None
		"""
		response=yield self.__res_manager.copy(s_key,s_bucket,d_key,d_bucket)
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
		response=yield self.__res_manager.delete(key,bucket or self.__bucket_name)
		return response
	@gen.coroutine
	def list(self,bucket=None,limit=1000,prefix="",delimiter="",marker=""):
		"""list  resource detail information that meet requirements
		Args:
			refer to qiniu document
		Returns:
			a list of resource information
		"""
		response=yield self.__res_manager.list(bucket or self._bucket,limit,prefix,delimiter,marker)
		return response
	@gen.coroutine
	def fetch_store(self,fetch_url,key=None,bucket=None):
		"""fecth resource of 'fecth_url' ,then save it to 'bucket'
		Args:
			fetch_url:fetch url
			key:resource saving key name
			bucket:resource saving bucket name
		Returns:
			None
		"""
		response=yield self.__res_manager.fetch_store(fetch_url,key,bucket or  self._bucket)
		return response
	@gen.coroutine
	def batch(self,*opers):
		""" execute multi resource management operations
		Args:
			*opers:opertions
		Returns:
			None
		"""
		response=yield self.__res_manager.batch(*opers)
		return response
	@gen.coroutine
	def prefetch(self,key,bucket=None):
		response=yield self.__res_manager.prefetch(key,bucket or self._bucket)
		return response
	@gen.coroutine
	def prefop(self,persistent_id):
		response=yield self.__res_processor.prefop(presistent_id)
		return response	
	def persistent(self,key,notify_url,fops=None,force=1,pipeline=None):
		return self.__res_processor.persistent(key,notify_url,self.__bucket_name,fops,force,pipeline)
		
	
