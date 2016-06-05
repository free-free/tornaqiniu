#-*- coding:utf-8 -*-
from resource_load import QiniuResourceLoader
from resource_manage import QiniuResourceManager
from resource_process import QiniuResourceProcessor
from resource import Resource
import functools



def rq_res(method):
	@functools.wraps(method)
	def wrapper(self,*args,**kwargs):
		if not self._resource_instance:
			raise Exception("'%s' has no such method '%s'"%(str(self),method.__name__))
		return method(self,*args,**kwargs)	
	return wrapper


class Bucket(object):
	def __init__(self,auth,bucket_name,bucket_acp=0):
		r"""
		Args:
			auth:qiniu authentication object
			bucket_name:bucket name
			bucket_acp: bucket access property
				0--->public bucket
				1--->private bucket
		"""
		self.__auth=auth
		self.__bucket_name=bucket_name
		self.__bucket_acp=bucket_acp
		self.__res_loader=QiniuResourceLoader(self.__auth,self.__bucket_name)
		self.__res_manager=QiniuResourceManager(self.__auth,self.__bucket_name)
		self.__res_processor=QiniuResourceProcessor(self.__atuh,self.__bucket_name)
		self._res_instance=None
	@property
	def acp(self):
		return self.__bucket_acp
	def resource(self,res_key):
		self._res_instance=Resource(res_key,self)
		return self._res_instance
	@rq_res 
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
	@rq_res
	def public_url(self,key):
		"""
		Args:
			key:resource key name
		Returns:
			resource public url
		"""
		return self._resource_loader.public_url(key)
	@rq_res
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
	@rq_res
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
	@rq_res
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
	@rq_res
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
	@rq_res
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
	@rq_res
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
	@rq_res
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
	@rq_res
	@gen.coroutine
	def prefecth(self,key,bucket=None):
		response=yield self._resource_manager.prefetch(key,bucket or self._bucket)
		return response
	
