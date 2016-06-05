#-*- coding:utf-8 -*-
from resource_load import *
from resource_process import *
from resource_manage import *


class Resource(object):
	r"""
		A map class  to qiniu bucket resource
	"""
	def __init__(self,key,bucket):
		r"""
		Args:
			key:resource key name,
			bucket:bucket object,
		"""
		self.__key=key
		self.__bucket=bucket
	def url(self,*args,**kwargs):
		pass
