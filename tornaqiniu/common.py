#-*- coding:utf-8 -*-
from datetime import datetime
from .utils import *
from tornado import gen
from tornado import httpclient
from tornado.httpclient import AsyncHTTPClient

class Auth(object):
	def __init__(self,access_key,secret_key):
		assert access_key!=None and access_key!="","invalid access_key"	
		assert secret_key!=None and secret_key!="","invalid secret_key"
		self.__access_key=access_key
		self.__secret_key=secret_key
	def upload_token(self,bucket,key=None,expires=3600,policys=None):
		assert bucket!=None and  bucket!="","invalid bucket"
		all_policys=policys or {}
		if 'scope' not in all_policys:
			if key:
				all_policys['scope']=bucket+':'+key
			else:
				all_policys['scope']=bucket
		if 'deadline' not in all_policys:
			all_policys['deadline']=int(datetime.timestamp(datetime.now()))+expires
		json_policys=json_encode(all_policys)
		b64_encoded_policys=urlsafe_base64_encode(json_policys)
		sha1_sign=hmac_sha1(self.__secret_key,b64_encoded_policys)
		b64_encoded_sign=urlsafe_base64_encode(sha1_sign)
		upload_token=self.__access_key+':'+bytes_decode(b64_encoded_sign)+':'+bytes_decode(b64_encoded_policys)
		return upload_token
	def download_token(self,download_url,expires=3600):
		url=download_url
		if download_url.find("?")>=0:
			url+="&e="+str(int(datetime.timestamp(datetime.now()))+expires)
		else:
			url+='?e='+str(int(datetime.timestamp(datetime.now()))+expires)
		download_token=self.access_token(url)
		return download_token
	def access_token(self,need_sign):
		sha1_sign=hmac_sha1(self.__secret_key,need_sign)			   
		b64_encoded_sign=urlsafe_base64_encode(sha1_sign)
		access_token="{0}:{1}".format(self.__access_key,bytes_decode(b64_encoded_sign))
		return access_token
	def callback_verify_header(self,url_path,body=None):
		signing_str=url_path+"\n"
		if body:
			signing_str+=body
		access_token=self.access_token(signing_str)
		return "QBox "+access_token

class QiniuResourceOperationBase(object):
	def __init__(self,bucket,auth):
		assert bucket!=None and bucket!="","invalid bucket"
		self._bucket=bucket
		self._auth=auth
	@gen.coroutine
	def send_async_request(self,url,headers=None,method="GET",body=None):
		headers=headers or {}
		if body or method.upper()=="POST":
			headers["Content-Type"]="application/x-www-form-urlencoded"
		req=httpclient.HTTPRequest(url,method=method,body=body,headers=headers,allow_nonstandard_methods=True)
		http_request=AsyncHTTPClient()
		response=""
		try:
			response=yield http_request.fetch(req)
		except httpclient.HTTPError as e:
			print("Error:"+str(e))
		except Exception as e:
			print("Error:"+str(e))
		else:
			return bytes_decode(response.body)
		finally:
			http_request.close()
