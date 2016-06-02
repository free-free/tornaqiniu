#-*- coding:utf-8 -*-
from tornado import gen,httpclient
from tornado.httpclient import AsyncHTTPClient
import json
from .resource_manage import QiniuResourseManageMixin
from .resource_load import QiniuResourceLoadMixin
from .resource_process import QiniuImageProcessMixin,QiniuResourceQRCodeMixin
from .errors import EncodingError
from .utils import bytes_encode,bytes_decode,urlsafe_base64_encode,json_encode,json_decode,hmac_sha1
import base64
import hmac
class QiniuClient(
		QiniuResourseManageMixin,
		QiniuResourceLoadMixin,
		QiniuImageProcessMixin,
		QiniuResourceQRCodeMixin	
		):
	def __init__(self,access_key,secret_key,download_host=None,bucket=None):
		assert isinstance(access_key,(str,bytes))
		assert isinstance(secret_key,(str,bytes))
		assert isinstance(bucket,(type(None),str,bytes))
		self._access_key=access_key
		self._secret_key=secret_key
		self._bucket=bucket
		self._download_host=download_host
		self._policys={}
	@gen.coroutine
	def _send_async_request(self,url,headers=None,method="GET",body=None):
		headers=headers or {}
		if body or method.upper()=="POST":
			headers['Content-Type']="application/x-www-form-urlencoded"
		req=httpclient.HTTPRequest(url,method=method,body=body,headers=headers,allow_nonstandard_methods=True)
		http_request=AsyncHTTPClient()
		response=""
		try:
			response=yield http_request.fetch(req)
		except httpclient.HTTPError as e:
			print("Error:"+str(e))
		else:
			return response.body.decode()
		finally:
			http_request.close()

	def _access_token(self,url_path,body=None):
		""" access token for Authorization"""
		signing_str=url_path+"\n"
		if body:
			signing_str=signing_str+body
		sign=hmac_sha1(self._secret_key,signing_str)
		encoded_sign=urlsafe_base64_encode(sign)
		access_token=self._access_key+":"+bytes_decode(encoded_sign)
		return access_token
	def _authorization(self,url_path,body=None):
		""" return http header for "Authorization" """
		return "QBox "+self._access_token(url_path,body)
	def _encode_entry(self,entry):
		""" encode entry"""
		return urlsafe_base64_encode(entry)



