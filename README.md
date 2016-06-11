## Description
	tornaqiniu is a qiniu cloud storage client for tornado

## Get Started:
###upload and download
```python
from tornado imoprt gen,ioloop
from tornaqiniu import QiniuClient

access_key="your qiniu access key"
secret_key="your qiniu secret key"
bucket="your bucket name"
domain="your domain"
bucket_acp=0   #bucket access property,1 ===>private bucket,0===>public bucket

client=QiniuClient(access_key,secret_key,domain)

#get a bucket instance
bucket=client.bucket(bucket,bucket_acp=1)

#get bucket upload token
bucket.upload_token()

# get resource url
bucket.res("resource_key").url()

# download resource
@gen.coroutine
def get_resource():
	response=yield bucket.res("resource_key").get()#return download file saved name
	print(response)
loop=ioloop.IOLoop.current()
loop.run_sync(get_resource)
loop.close()
```

## Updating
	..............
  

