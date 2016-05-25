#-*- coding:utf-8 -*-
from tornado import gen
from bucket import QiniuResourseManageMixin

class QiniuClient(QiniuResourseManageMixin):
	def __init__(self,access_key,secret_key,bucket=None):
		assert isinstance(access_key,(str,bytes))
		assert isinstance(secret_key,(str,bytes))
		assert isinstance(bucket,(type(None),str,bytes))
		self.__access_key=access_key
		self.__secret_key=secret_key
		self.__bucket=bucket
	
		
