#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import hashlib
import base64
from datetime import datetime
from .errors import EncodingError
from . import PUT_POLICY
class QiniuResourceUploadMixin(object):	
	def upload_token(self,bucket=None,key=None,expires=3600,policys=None):
		if not bucket:
			bucket=self._bucket
			assert bucket!=None,"bucket can't be empty"
		if policys:
			self._policys=policys
		if 'scope' not in self._policys:
			if key:
				self._policys['scope']=bucket+":"+key
			else:
				self._policys['scope']=bucket
		if 'deadline' not in self._policys:
			self._policys['deadline']=int(datetime.timestamp(datetime.now()))+expires	
		#josn encode policys
		json_policys=self._json_encode(self._policys)
		#base64 encode
		b64_encoded_policys=self._urlsafe_base64_encode(self._bytes_encode(json_policys))	
		sha1_sign=hmac.new(self._bytes_encode(self._secret_key),b64_encoded_policys,'sha1').digest()
		b64_encoded_sign=self._urlsafe_base64_encode(sha1_sign)
		upload_token=self._access_key+":"+self._bytes_decode(b64_encoded_sign)+":"+self._bytes_decode(b64_encoded_policys)
		self._policys={}
		return upload_token
			
		
			
