#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import base64
import urllib
from .utils import *


class _QiniuResourceOpsInterface(object):
	"""
		this class defines all qiniu resource prosession interface 
	"""
	_gravity_map={1:"NorthWest",2:"North",3:"NorthEast",
		     4:"West",5:"Center",6:"East",
		     7:"SouthWest",8:"South",9:"SouthEast"}
	def image_watermark_interface(self,
			   water_image_url,
			   dissolve=100,
			   gravity=9,
			   dx=10,
			   dy=10,
			   ws=0):
		r"""
			The detail definition of parameters,please refer to qiniu documents
		"""
		assert isinstance(dissolve,int) and dissolve>=1 and dissolve<=100
		assert isinstance(gravity,int) 
		assert isinstance(dx,int) and isinstance(dy,int)
		assert float(ws)>=0.0 and float(ws)<=1.0
		interface="watermark/1"
		interface+='/image/'+str(bytes_decode(urlsafe_base64_encode(water_image_url)))
		interface+='/dissolve/'+str(dissolve)
		interface+='/gravity/'+str(self._gravity_map.get(gravity,"SouthEast"))
		interface+='/dx/'+str(dx)
		interface+='/dy/'+str(dy)
		interface+='/ws/'+str(ws)
		return interface
	
	def text_watermark_interface(self,
				text,
				font="宋体",
				font_size=500,
				fill="#ffffff",
				dissolve=100,
				gravity=9,
				dx=10,
				dy=10):
		r"""
			The detail  definition of parameters,please refer to qiniu documents
		"""
		assert isinstance(font,str)
		assert isinstance(font_size,int)
		assert isinstance(fill,str)
		assert isinstance(dissolve,int) and dissolve>=1 and dissolve<=100
		assert isinstance(gravity,int)
		assert isinstance(dx,int) and isinstance(dy,int)
		interface="watermark/2"
		interface+='/text/'+str(bytes_decode(urlsafe_base64_encode(text)))
		interface+='/font/'+str(bytes_decode(urlsafe_base64_encode(font)))
		interface+='/fontsize/'+str(font_size)
		interface+='/fill/'+str(bytes_decode(urlsafe_base64_encode(fill)))
		interface+='/dissolve/'+str(dissolve)
		interface+='/gravity/'+str(self._gravity_map.get(gravity,"SouthEast"))
		interface+='/dx/'+str(dx)
		interface+='/dy/'+str(dy)
		return interface

	def image_view2_interface(self,mode,width=None,height=None,frmt=None,interlace=0,quality=75,ignore_error=0):
		r"""
			qiniu imageView2 procession
			
			@parameters:
				'url':image url,
				'mode':image procession mode,the specific definition as follows:
					1.mode 0:
						image's long edge max is 'width',image's short edge max is 'height' and 
						don't perform cut opertion.If just specific 'witdh' or 'height' ,
						then another edge will be self-adjust.
					2.mode 1:
						images' min width is 'width' and min heigth is 'height'.
						performing middle cut opertion.If just specific 'width' or 'height',
						then width will be equal to height
					3.mode 2:
						this mode almost be same with mode 0,the only difference is mode 2 
						limit images' width and height.mode 0 is suitable for mobile ,
						mode 2 is suitable for PC
					4.mode 3:
						image's  min width is 'width' and min height is 'height',
						don't perform cut opertions.If just specific 'width' or 'height',
						then widht will be equal to height
					5.mode 4:
						..............
					6.mode 5:	
						.............
				'width':image processed width,
				'height':image processed height,
				'frmat':image format,supporting .jpg,.gif,.png,.webp,
				'interlace':image interlace show,the default values is true
				'quality':image processed quality,range from 0 to 100,the default value is 75,
				'ignore-error':whether to ignore error,when image procession failed!.the default value is true
		"""
		assert mode<6 and mode>=0,"'mode' must range from 0 to 5"
		assert width or height,"both 'width' and 'height' can't be none "
		assert quality<=100 and quality>=0,"'quality' must range from 0 to 100"
		interface="imageView2/"+str(mode)
		if width:
			interface='/w/'+str(width)
		if height:
			interface='/h/'+str(width)
		if frmt:
			interface='/format/'+str(frmt)
		if interlace!=0:
			interface='/interlace/'+str(interlace)
		if quality!=75:
			interface='/quality/'+str(quality)
		if ignore_error!=0:
			interface+='/ignore-error/'+str(ignore_error)
		return interface

	def qrcode_interface(self,mode,level):
		_level_map={1:"L",2:"M",3:"Q",4:"H"}
		r"""
			generate QR code for resource 
			
			@parameter:
				1.download_url:resource download url,
				2.mode: 0 or 1,
				3.level: QR code image size,the value
				range from 1 to 4
		"""
		assert int(mode)==0 or int(mode)==1,"'mode' must be 0 or 1"
		assert int(level) in [1,2,3,4],"'level' must range from 1 to 4"
		interface="qrcode/"+str(mode)+'/level/'+str(_level_map.get(level))
		return interface
	def avthumb_transcoding_interface(self,frmt,**options):
		"""
			The  'options' parameter  detail definition refers to :
				 http://developer.qiniu.com/code/v6/api/dora-api/av/avthumb.html
		"""
		interface="avthumb/%s"%str(frmt)
		if len(options)>0:
			interface+=self._options_dict_to_str(options)
		return interface
	def _options_dict_to_str(self,options):
		options_list=list(options.items())
		options_list=list(map(lambda item:"/"+str(item[0])+"/"+str(item[1]),options_list))
		options_str=reduce(lambda op1,op2:op1+op2,options_list)
		return options_str
	def avthumb_slice_interface(self,no_domain,**options):
		"""
			'options' detail definition refer to:
				http://developer.qiniu.com/code/v6/api/dora-api/av/segtime.html
		"""
		interface="avthumb/m3u8/noDomain/%s"str(if int(no_domain)>0 1 else 0)
		if len(options)>0:
			interface+=self._options_dict_to_str(options)
		return interface
	def avconcat_interface(self,mode,frmt,*encoded_urls):
		"""
			detail refer to:
				http://developer.qiniu.com/code/v6/api/dora-api/av/avconcat.html
		"""
		interface="avconcat/"+str(mode)+'/format/'+str(frmt)
		for encoded_url in encoded_urls:
			interface+='/'+encoded_url
		return interface
	def vframe_interface(self,out_img_frmt,offset,width=None,heigth=None,rotate=None):
		"""
			detail definition refer to:
				http://developer.qiniu.com/code/v6/api/dora-api/av/vframe.html
		"""
		interface='vframe/'+str(out_img_frmt)+'/offset/'+str(offset)
		if width:
			assert width>=1 and width<=3840
			interface+='/w/'+str(width)
		if heigth:
			assert heigth>=1 and height<=2160
			interface+='/h/'+str(height)
		if rotate:
			assert rotate in [90,180,270,'auto']
			interface+='/rotate/'+str(rotate)
		return interface
	def vsample_interface(self,out_img_frmt,
			     start_second,
			     sample_time,
			     resolution_width=None,
		             resolution_height=None,
			     rotate=None,
			     sample_interval=None,
			     pattern=None):
		"""
			detail definition refer to:
				http://developer.qiniu.com/code/v6/api/dora-api/av/vsample.html
		"""
		interface="vsample/"+str(out_img_frmt)+'/ss/'+str(start_second)
		interface+='/t/'+str(sample_time)
		if resolution_width and resolution_height:
			assert resolution_width>=1 and resolution_width<=1920
			assert resolution_height>=1 and resolution_height<=1080
			interface+='/s/'+str(resolution_width)+'x'+str(resolution_height)
		if rotate:
			assert rotate in (90,180,270,'auto')
			interface+='/rotate/'+str(rotate)
		if sample_interval:
			interface+='/interval/'+str(sample_intervale)
		if pattern:
			interface+=bytes_decode(urlsafe_base64_encode(pattern))
		return 	interface
	

			
			 	
class QiniuImageProcessMixin(object):
	def image_view2(self,url,mode,width=None,height=None,frmt=None,interlace=0,quality=75,ignore_error=0):
		interface=self.image_view2_interface(mode,width,height,frmt,interlace,quality,ignore_error)
		resulted_url=url
		if url.find("?")>=0:
			resulted_url+="&"+interface
		else:
			resulted_url+="?"+interface
		return resulted_url
	def image_watermark(self,origin_url,water_image_url,dissolve=100,gravity=9,dx=10,dy=10,ws=0):
		watermark_interface=self.image_watermark_interface(water_image_url,dissolve,gravity,dx,dy,ws)
		resulted_url=origin_url
		if origin_url.find("?")>=0:
			resulted_url+='&'+watermark_interface
		else:
			resulted_url+='?'+watermark_interface
		return resulted_url	

	def text_watermark(self,origin_url,text,font="宋体",font_size=500,fill="#000",dissolve=100,gravity=9,dx=10,dy=10):
		watermark_interface=self.text_watermark_interface(text,font,font_size,fill,dissolve,gravity,dx,dy)
		resulted_url=origin_url
		if origin_url.find("?")>=0:
			resulted_url+='&'+watermark_interface
		else:
			resulted_url+="?"+watermark_interface
		return resulted_url
	def multi_watermark(self,origin_url,*args):
		"""
			multi watermark parameters are too much,
			so i decided to implement it at the next time.
		"""
		pass
	def imageinfo_url(self,origin_url):
		if origin_url.find("?")>=0:
			return origin_url+"&imageInfo"
		else:
			return origin_url+"?imageInfo"
	def multi_imageinfo_url(self,urls,key_name=None):
		if isinstance(urls,(list,tuple)):
			info_urls=[]
			if key_name:
				# for 'list' or 'tuple' like this:[{"key1":"xx","key2":"21"},{..},{..},...]
				for url in urls:
					info_urls.append(self.imageinfo_url(url[key_name]))
			else:
				# for 'list' or 'tuple'  like this: [url1,url2,....]
				for url in urls:
					info_urls.append(self.imageinfo_url(url))
			return info_urls
		return None
	@gen.coroutine
	def get_imageinfo(self,origin_url):
		url=self.imageinfo_url(origin_url)
		response=yield self._send_async_request(url)
		if response:
			return json_decode(response)
	def imageexif_url(self,origin_url):
		if origin_url.find("?")>=0:
			return origin_url+'&exif'
		else:
			return origin_url+'?exif'
	def multi_imageexif_url(self,urls,key_name=None):
		if isinstance(urls,(list,tuple)):
			exif_urls=[]
			if key_name:
				for url in urls:
					exif_urls.append(self.imageexif_url(url[key_name]))
			else:
				for url in urls:
					exif_urls.append(self.imageexif_url(url))
			return exif_urls
	@gen.coroutine
	def get_imageexif(self,origin_url):
		url=self.imageexif_url(origin_url)
		response=yield self._send_async_request(url)
		return response							
	def imageave_url(self,origin_url):
		if origin_url.find("?")>=0:
			return origin_url+'&imageAve'
		else:
			return origin_url+'?imageAve'
	def multi_imageave_url(self,urls,key_name):
		if  isinstance(urls,(list,tuple)):
			ave_urls=[]
			if key_name:
				for url in urls:
					ave_urls.append(self.imageave_url(url[key_name]))
			else:
				for url in urls:
					ave_urls.append(self.iamgeave_url(url))
			return ave_urls
	@gen.coroutine
	def get_imageave(self,origin_url):
		url=self.imageave_url(origin_url)
		response=yield self._send_async_request(url)
		if response:
			return json_decode(response).get("RGB")

class QiniuResourceQRCodeMixin(object):	
	def qrcode_url(self,url,mode=0,level=1):
		resulted_url=url
		interface=self.qrcode_interface(mode,level)
		if url.find("?")>=0:
			resulted_url+='&'+interface
		else:
			resulted_url+='?'+interface
		return resulted_url



class QiniuResourceMDToHTMLMixin(object):
	"""
		convert mardown to html
		@parameters:
			1.mode:0 or 1
			2.css: url of css style
	"""
	def _md2html_url(self,url,mode,css):
		assert int(mode)==0 or int(mode)==1,"'mode' must be 0 or 1"
		interface="md2html/"+str(mode)+'/css/'+bytes_decode(urlsafe_base64_encode(css))
		resulted_url=url
		if resulted_url.find("?")>=0:
			resulted_url+="?"+interface
		else:
			resulted_url+='&'+interface
		return resulted_url

class QiniuResourceAVMixin(object):
	def avinfo_url(self,av_url):
		if av_url.find("?")>=0:
			return av_url+"&avinfo"
		else:
			return av_url+"?avinfo"
	@gen.coroutine
	def get_avinfo(self,av_url):
		avinfo_url=self.avinfo_url(av_url)
		response=yield self._send_async_request(avinfo_url)
		if response:
			return json_decode(response)
		return None
	
		
class QiniuResourcePersistentMixin(object):
	@gen.coroutine
	def _send_persistent_request(self,url_path,host="api.qiniu.com",body=None,method=None):
		url="http://"+host+url_path
		headers={}
		headers['Authorization']=self._authorization(url_path,body)
		headers['Host']=host
		response=yield self._send_async_request(url,headers=headers,method=method or "POST",body=body)
		return response	
	@gen.coroutine
	def persistent(self,key,fops,notify_url,bucket=None,force=1,pipeline=None):
		bucket=bucket or self._bucket
		assert bucket,"bucket can't be none"
		body=urlencode({
			'bucket':bucket,
			'key':key,
			'fops':fops,
			'notifyURL':notify_url,
			'pipeline':pipeline or "",
			'force':force
		})
		response=yield self._send_persistent_request('/pfop/',body=body)
		return response
		

			
