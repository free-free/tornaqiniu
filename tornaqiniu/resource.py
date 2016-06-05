#-*- coding:utf-8 -*-
from resource_load import *
from resource_process import *
from resource_manage import *


class Resource(object):
	r"""
		A map class  to qiniu bucket resource
	"""
	def __init__(self,key,bucket,res_loader,res_manager=None,res_processor=None):
		r"""
		Args:
			key:resource key name,
			bucket:bucket object,
			res_loader:resource loader,
			res_manager:resource manager,
			res_processor:resource processor,
		"""
		self.__key=key
		self.__bucket=bucket
		self.__res_loader=res_loader
		self.__res_manager=res_manager
		self.__res_processor=res_processor
	def url(self,*args,**kwargs):
		pass
