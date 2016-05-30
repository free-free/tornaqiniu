#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import hashlib
import base64
from datetime import datetime
from .errors import EncodingError,PolicyKeyError,PolicyValueTypeError
from . import PUT_POLICY
class QiniuResourceLoadMixin(object):	
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
		b64_encoded_policys=self._urlsafe_base64_encode(json_policys)	
		sha1_sign=self._hamc_sha1(self._secret_key,b64_encoded_policys)
		b64_encoded_sign=self._urlsafe_base64_encode(sha1_sign)
		upload_token=self._access_key+":"+self._bytes_decode(b64_encoded_sign)+":"+self._bytes_decode(b64_encoded_policys)
		self._policys={}
		return upload_token
	def _check_policy(self,field,value):
		if policy_field not in PUT_POLICY.keys():
				raise PolicyKeyError("Not support '%s' policy"%policy_field)		
		if not isinstance(policy_value,PUT_POLICY[policy_field]['type']):
				raise PolicyValueTypeError("Policy '%s' value type error"%policy_field)
	def add_policy(self,policy_field,policy_value):
		self._check_policy(policy_field,policy_value)
		self._policys[policy_field]=policy_value
	def add_policys(self,policy_pairs):
		for key,value in policy_pairs.items():
			self._check_policy(key,value)
			self._policys[key]=value
	@property
	def policys(self):
		return self._policys
	def _gen_private_url(self,key,expires=3600,host=None):
		if not host:
			host=self._download_host
			assert host!=None,"download host can' be empty"
		if not host.startswith("http://"):
			host="http://"+host
		download_url=host+key+"?="+str(int(datetime.timestamp(datetime.now()))+expires)
		sha1_sign=self._hamc_sha1(self._secret_key,download_url)
		b64_encoded_sign=self._urlsafe_base64_encode(sha1_sign)
		token=self._access_key+":"+self._bytes_decode(b64_encoded_sign)
		return token
	def private_url(self,key,expires=3600,host=None):
		r"""
			generate one private url 
			
			@parameters:
				key:resource key,'str' type,
				expires:'int' type,units:'s',
				host:resource host name
		"""
		return self._gen_private_url(key,expires,host)
	def private_urls(self,keys,expires=3600,host=None,key_name=None):
		"""
			generate multi private urls at the same time
		
			@parameters
				keys:resource keys ,'list','dict' or  'tuple' type,
				expires:int type,units:'s',
				host:resource host name,
				key_name:when  'keys' type  is 'dict',your must point out key name in 'keys'
			@return:
				download_urls: 'list' typw
		"""
		download_urls=[]
		if isinstance(keys,(list,tuple)):
			for key in keys:
				download_urls.append(self._gen_private_url(key,expires,host))
			return download_urls
		elif isinstance(keys,dict) and key_name:
			for field in keys.items():
				download_urls.append(self._gen_private_url(field[key_name],expires,host))
		else:
			pass
		return download_urls
	def _gen_public_url(self,key,host=None):
		if not host:
			host=self._download_host
			assert host!=None,"download host can't be empty"
		if not host.startswith("http://"):
			host="http://"+host
		download_url=host+key
		return download_url
	def public_url(self,key,host=None):
		r"""
			generate public url 
			
			@parameters:
				key:resource key,'str' type,
				host:resource host name
		"""
		return self._gen_public_url(key,host)
	def public_urls(self,keys,host=None,key_name=None):
		r"""
			generate multi public url
			the parameters difinition is same with 'private_urls'
		"""
		download_urls=[]
		if isinstance(keys,(tuple,list)):
			for key in keys:
				download_urls.append(self._gen_public_url(key,host))
			return download_urls
		elif isinstance(keys,dict) or key_name:
			for field in keys.itmes():
				download_urls.append(self._gen_public_url(field[key_name],host))
		else:
			pass
		return download_urls	
	
	
