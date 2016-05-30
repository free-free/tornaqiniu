#-*- coding:utf-8 -*-
from tornado import gen,httpclient
import hmac
import base64



class QiniuImageProcessMixin(object):
	def image_view2(self,url,mode,width=None,height=None,frmt=None,interlace=0,quality=75,ignore_error=0):
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
		p_pattern=""
		p_pattern+="imageView2/"+str(mode)
		if width:
			p_pattern+='/w/'+str(width)
		if height:
			p_pattern+='/h/'+str(width)
		if frmt:
			p_pattern+='/format/'+str(frmt)
		if interlace!=0:
			p_pattern+='/interlace/'+str(interlace)
		if quality!=75:
			p_pattern+='/quality/'+str(quality)
		if ignore_error!=0:
			p_pattern+='/ignore-error/'+str(ignore_error)
		if url.find("?"):
			url+="&"+p_pattern
		else:
			url+="?"+p_pattern
		return url

			
		
