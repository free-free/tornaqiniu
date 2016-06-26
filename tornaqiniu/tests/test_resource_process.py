#-*- coding:utf-8 -*-
from tornado import gen
import tornado.ioloop
from tornaqiniu import QiniuClient
import time

access_key='CKQNXugLAXFueA5UlBKQnkWxslYC8rIErwn2ch4I'
secret_key='4lnKaSKUk1SVmbB4alt6PtkL2O1Sm-jP6e-T7EER'
bucket="static-pyblog-com"
domain='7xs7oc.com1.z0.glb.clouddn.com'

if __name__=='__main__':
	print(time.time())
	client=QiniuClient(access_key,secret_key,host=domain)
	""" testing public resource text watermark"""
	#url=client.public_url("image/java.jpg")
	#print(client.text_watermark(url,"hello",fill="#000",font_size=200))
	""" testing public resource image watermark"""
	#water_image_url=client.public_url("image/python.jpg")
	#origin_image_url=client.public_url("image/java.jpg")
	#print(client.image_watermark(origin_image_url,water_image_url,ws=1))
	""" testing private resource text watermark"""
	#url=client.private_url("image/java.jpg")
	#print(client.text_watermark(url,"fuck",fill="#000"))
	""" testing private resource image watermark"""
	#water_image_url=client.private_url("image/python.jpg")
	#origin_image_url=client.private_url("image/java.jpg")
	#print(client.image_watermark(origin_image_url,water_image_url,ws=1))
	""" testing get image information"""
	#public_url=client.public_url("image/java.jpg")
	#public_url=client.imageinfo_url(public_url)
	#print(public_url)
	#private_url=client.private_url("image/java.jpg")
	#private_url=client.imageinfo_url(private_url)
	#print(private_url)
	#@gen.coroutine
	#def go():
		#url=client.public_url("image/java.jpg")
	#	url=client.private_url("image/java.jpg")
	#	info=yield client.get_imageinfo(url)
	#	print(info)
	""" testing image exif"""
	#public_url=client.public_url("image/java.jpg")
	#public_url=client.imageexif_url(public_url)	
	#print(public_url)
	#@gen.coroutine
	#def go():
	#	url=client.public_url("image/java.jpg")
	#	info=yield client.get_imageexif(url)
	#	print(info)
	""" testing image ave"""
	#url=client.public_url("image/java.jpg")
	#print(client.imageave_url(url))
	bucket=client.bucket(bucket,bucket_acp=0)
	@gen.coroutine	
	def go():
		pass
		#batch=bucket.res("image/python.jpg").batch()
		#batch.stat()
		#batch.delete("pystonic.jpg")
		#batch.delete("zzzz/python.jpg")
		#info=yield batch.execute()
		#info=yield bucket.res(*["image/python.jpg","image/java.jpg"]).multi_stat()
		#info=bucket.res(*["image/python.jpg","image/java.jpg"]).imageinfo().url()
		#info=bucket.res(*["image/python.jpg","image/java.jpg"]).url()
		#info=yield bucket.res(*["image/python.jpg","image/java.jpg"]).get()
		#info=yield bucket.res(*["image/python.jpg","image/java.jpg","image/php.jpg","image/linux.jpg"]).get()
		#qrcode=bucket.qrcode()
		#info=bucket.res("image/python.jpg").fops(qrcode).url()
		#info=yield bucket.res("image/python.jpg").get()
		#info=bucket.res("image/python.jpg").imageinfo().url()
		#info=yield bucket.res("image/python.jpg").imageinfo().get()
		#info=bucket.res("image/python.jpg").imageave().url()
		#info=yield bucket.res("image/python.jpg").imageave().get()
		#info=bucket.res("image/python.jpg").imageexif().url()
		#info=yield bucket.res("image/python.jpg").imageexif().get()
		#info=yield bucket.res().list()
		#info=yield bucket.res("image/python.jpg").stat()
		#info=yield bucket.res("zzzz/java.jpg").delete()
		#info=yield bucket.res("image/python.jpg").copyto("python.jpg")
		#info=yield bucket.res("python.jpg").moveto("zzzz/python.jpg")
		#print(bucket.res("image/python.jpg").fops().qrcode().url())
		#info=yield bucket.res("image/python.jpg").fops().qrcode().get()
		#info=bucket.res("image/python.jpg","image/java.jpg").fops().qrcode().url()
		#info=yield bucket.res("image/python.jpg","image/java.jpg").fops().qrcode().get()
		#print(bucket.res("image/linux.jpg").fops().text_watermark("Shabi").url())
		#p_bucket=client.bucket(bucket,bucket_acp=1)
		#water_img_url=p_bucket.res("image/down3.jpg").url()
		#print(water_img_url)
		#print(bucket.res("image/python.jpg").fops().image_watermark(water_img_url).qrcode().url())
		#print(bucket.res("image/python.jpg","image/java.jpg").fops().text_watermark("sb").saveas(["tw_python.jpg","tw_java.jpg"]).url())
		
		info=yield bucket.res("image/python.jpg","image/java.jpg").fops().text_watermark("sb").saveas(["tw_python.jpg","tw_java.jpg"]).get()
		print(info)	
	loop=tornado.ioloop.IOLoop.current()
	loop.run_sync(go)
	loop.close()
	print(time.time())

	
	


