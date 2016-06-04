#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import hashlib
import base64
from   datetime import datetime
from   .errors import EncodingError,PolicyKeyError,PolicyValueTypeError
from   .utils import urlsafe_base64_encode,bytes_encode,bytes_decode,hmac_sha1,json_encode,json_decode
from   . import PUT_POLICY
from .common import Auth,QiniuResourceOperationBase
class QiniuResourceLoader(QiniuResourceOperationBase):
	def __init__(self,bucket,auth):
		super(QiniuResourceLoader,self).__init__(bucket,auth)
		self._download_host=""
		self._policys={}
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
	def get_flush_policys(self):
		policys=self._policys
		self._policys={}
		return policys
	def _gen_private_url(self,key,host,expires=3600):
		assert host!=None and host!="","download host can' be empty"
		if not host.startswith("http://"):
			host="http://"+host
		download_url=host+'/'+key
		token=self._auth.download_token(download_url,expires=expires)
		download_url+='?e='+str(int(datetime.timestamp(datetime.now()))+expires)
		download_url+="&token="+token
		return download_url
	def private_url(self,key,host,expires=3600):
		r"""
			generate one private url 
			
			@parameters:
				key:resource key,'str' type,
				expires:'int' type,units:'s',
				host:resource host name
		"""
		return self._gen_private_url(key,expires,host)
	def private_urls(self,keys,host,expires=3600,key_name=None):
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
			if key_name:
				for key in keys:
					download_urls.append(self._gen_private_url(key[key_name]),expires,host)
			else:
				for key in keys:
					download_urls.append(self._gen_private_url(key,expires,host))
		else:
			pass
		return download_urls
	def _gen_public_url(self,key,host):
		assert host!=None and host!=""," host can't be empty"
		if not host.startswith("http://"):
			host="http://"+host
		download_url=host+'/'+key
		return download_url
	def public_url(self,key,host):
		r"""
			generate public url 
			
			@parameters:
				key:resource key,'str' type,
				host:resource host name
		"""
		return self._gen_public_url(key,host)
	def public_urls(self,keys,host,key_name=None):
		r"""
			generate multi public url
			the parameters difinition is same with 'private_urls'
		"""
		download_urls=[]
		if isinstance(keys,(tuple,list)):
			if key_name:
				for key in keys:
					download_urls.append(self._gen_public_url(key[key_name],host))
			else:
				for key in keys:
					download_urls.append(self._gen_public_url(key,host))
		else:
			pass
		return download_urls	
	
	
