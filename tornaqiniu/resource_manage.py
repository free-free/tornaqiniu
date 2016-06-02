#-*- coding:utf-8 -*_
from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado import httpclient
import base64
import hmac
import urllib
from urllib import request

class QiniuResourseManageMixin(object):
	@gen.coroutine
	def _send_manage_request(self,url_path,host="rs.qiniu.com",body=None,method=None):
		full_host="http://"+host
		url=full_host+url_path
		headers={
			"Authorization":self._authorization(url_path,body),
			"Host":host
		}
		response=yield self._send_async_request(url,headers=headers,method=method or "GET",body=body)
		return response
	@gen.coroutine
	def stat(self,bucket,key):
		entry=bucket+":"+key
		encoded_entry=self._bytes_decode(self._encode_entry(entry))
		response= yield self._send_manage_request("/stat/"+encoded_entry)
		return response
	@gen.coroutine
	def move(self,src_bucket,src_key,dest_bucket,dest_key):
		src_entry=self._bytes_decode(self._encode_entry(src_bucket+':'+src_key))
		dest_entry=self._bytes_decode(self._encode_entry(dest_bucket+':'+dest_key))
		response=yield self._send_manage_request("/move/"+src_entry+'/'+dest_entry,method="POST")
		return response
	@gen.coroutine
	def modify_mime(self,bucket,key,mine_type):
		pass

	@gen.coroutine
	def copy(self,src_bucket,src_key,dest_bucket,dest_key):
		src_encoded_entry=self._bytes_decode(self._encode_entry(src_bucket+":"+src_key))
		dest_encoded_entry=self._bytes_decode(self._encode_entry(dest_bucket+":"+dest_key))
		response=yield self._send_manage_request("/copy/"+src_encoded_entry+"/"+dest_encoded_entry,method="POST")
		return response
	@gen.coroutine
	def delete(self,bucket,key):
		encoded_entry=self._bytes_decode(self._encode_entry(bucket+":"+key))
		response =yield self._send_manage_request("/delete/"+encoded_entry,method="POST")
		return response
	@gen.coroutine
	def list(self,bucket,limit=1000,prefix="",delimiter="",marker=""):
		assert limit>1 and limit<=1000,"limit must bettween 1 to 1000"
		query_string=urllib.parse.urlencode({
			'bucket':bucket,
			'limit':limit,
			'marker':marker,
			'prefix':prefix,
			'delimiter':delimiter,
		})	
		response=yield self._send_manage_request('/list?'+query_string,host="rsf.qbox.me",method="POST")
		return response
	@gen.coroutine
	def fetch_store(self,fecth_url,bucket,key=None):
		if key:
			encoded_entry=self._bytes_decode(self._encode_entry(bucket+":"+key))
		else:
			encode_entry=self._bytes_decode(self._encode_entry(bucket))
		encoded_fecth_url=self._bytes_decode(self._encode_entry(fetch_url))
		response=yield self._send_manage_request('/fetch/'+encoded_fetch_url+'/to/'+encoded_entry,host='iovip.qbox.me',method="POST")
		return response
	@gen.coroutine
	def batch(self,*opers):
		opertions={}
		for oper in opers:
			opertions['op']=oper
		opertions_body=urllib.parse.urlencode(opertions)
		response=yield self._send_manage_request('/batch',method="POST",body=opertions_body)
		return response
	@gen.coroutine
	def prefecth(self,bucket,key):
		encoded_entry=self._bytes_decode(self._encode_entry(bucket+':'+key))
		response=yield self._send_manage_request('/prefecth/'+encoded_entry,method="POST",host="iovip.qbox.me")
		return response
	
		
		
		
