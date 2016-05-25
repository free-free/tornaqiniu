#-*- coding:utf-8 -*-
from tornado import gen
from .resource_manage import QiniuResourseManageMixin

class QiniuClient(QiniuResourseManageMixin):
	def __init__(self,access_key,secret_key,bucket=None):
		assert isinstance(access_key,(str,bytes))
		assert isinstance(secret_key,(str,bytes))
		assert isinstance(bucket,(type(None),str,bytes))
		self._access_key=access_key
		self._secret_key=secret_key
		self._bucket=bucket
	def _urlsafe_base64_encode(self,policy):
		if isinstance(policy,str):
			return base64.urlsafe_b64encode(policy.encode("utf-8")).decode("utf-8")
		elif isinstance(polict,bytes):
			return base64.urlsafe_b64encode(policy).decode("utf-8")
		else:
			raise EncodingError("'policy' must be str or bytes type")
	
		
