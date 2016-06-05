#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import hashlib
import base64
from datetime import datetime
from .errors import *
from .utils import *
from . import PUT_POLICY
from .common import Auth,QiniuResourceOperationBase

class QiniuResourceLoader(QiniuResourceOperationBase):
	def __init__(self,bucket,auth):
		super(QiniuResourceLoader,self).__init__(bucket,auth)
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
	def delete_policy(self,field):
		if field in self._policys:
			del self._policys[field]
	def delete_policys(self,fields):
		for field in fields:
			self.delete_policy(field)
	def delete_all_policys(self):
		del self._policys
		self._policys={}
	def modify_policy(self,field,value):
		self._policys[field]=value
	@property
	def policys(self):
		return self._policys
	def get_policys(self):
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

	
	
class _Batch(object):
	def __init__(self,client):
		self.__client=client
		self.__operations=[]
	@gen.coroutine
	def execute(self):
		pass
	def __setattr__(self,attr,value):
		pass

class QiniuResourceManager(QiniuResourceOperationBase):
	def __init__(self,bucket,auth):
		super(QiniuResourceManager,self).__init__(bucket,auth)
	@gen.coroutine
	def _send_manage_request(self,url_path,host="rs.qiniu.com",body=None,method=None):
		full_host="http://"+host
		url=full_host+url_path
		headers={
			"Authorization":self._auth.callback_verify_header(url_path,body),
			"Host":host
		}
		response=yield self.send_async_request(url,headers=headers,method=method or "GET",body=body)
		return response
	@gen.coroutine
	def stat(self,key,bucket=None):
		bucket=bucket or self._bucket
		entry=bucket+":"+key
		encoded_entry=bytes_decode(urlsafe_base64_encode(entry))
		response= yield self._send_manage_request("/stat/"+encoded_entry)
		return response
	@gen.coroutine
	def move(self,src_bucket,src_key,dest_bucket,dest_key):
		src_entry=bytes_decode(urlsafe_base64_encode(src_bucket+':'+src_key))
		dest_entry=bytes_decode(urlsafe_base64_encode(dest_bucket+':'+dest_key))
		response=yield self._send_manage_request("/move/"+src_entry+'/'+dest_entry,method="POST")
		return response
	@gen.coroutine
	def modify_mime(self,bucket,key,mine_type):
		pass

	@gen.coroutine
	def copy(self,src_bucket,src_key,dest_bucket,dest_key):
		src_encoded_entry=bytes_decode(urlsafe_base64_encode(src_bucket+":"+src_key))
		dest_encoded_entry=bytes_decode(urlsafe_base64_encode(dest_bucket+":"+dest_key))
		response=yield self._send_manage_request("/copy/"+src_encoded_entry+"/"+dest_encoded_entry,method="POST")
		return response
	@gen.coroutine
	def delete(self,key,bucket=None):
		bucket=bucket or self._bucket
		encoded_entry=bytes_decode(urlsafe_base64_encode(bucket+":"+key))
		response =yield self._send_manage_request("/delete/"+encoded_entry,method="POST")
		return response
	@gen.coroutine
	def list(self,bucket=None,limit=1000,prefix="",delimiter="",marker=""):
		bucket=bucket or self._bucket
		assert limit>1 and limit<=1000,"limit must bettween 1 to 1000"
		query_string=urlencode({
			'bucket':bucket,
			'limit':limit,
			'marker':marker,
			'prefix':prefix,
			'delimiter':delimiter,
		})	
		response=yield self._send_manage_request('/list?'+query_string,host="rsf.qbox.me",method="POST")
		return response
	@gen.coroutine
	def fetch_store(self,fecth_url,key=None,bucket=None):
		bucket=bucket or self._bucket
		if key:
			encoded_entry=bytes_decode(urlsafe_base64_encode(bucket+":"+key))
		else:
			encode_entry=bytes_decode(urlsafe_base64_encode(bucket))
		encoded_fecth_url=bytes_decode(urlsafe_base64_encode(fetch_url))
		response=yield self._send_manage_request('/fetch/'+encoded_fetch_url+'/to/'+encoded_entry,host='iovip.qbox.me',method="POST")
		return response
	@gen.coroutine
	def batch(self,*opers):
		opertions={}
		for oper in opers:
			opertions['op']=oper
		opertions_body=urlencode(opertions)
		response=yield self._send_manage_request('/batch',method="POST",body=opertions_body)
		return response
	@gen.coroutine
	def prefecth(self,key,bucket=None):
		bucket=bucket or self._bucket
		encoded_entry=bytes_decode(urlsafe_base64_encode(bucket+':'+key))
		response=yield self._send_manage_request('/prefecth/'+encoded_entry,method="POST",host="iovip.qbox.me")
		return response
	
		
		
		
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
