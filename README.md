## Description
	tornaqiniu is a qiniu cloud storage client for tornado

## Get Started:
### 1.upload and download
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

# upload resource
@gen.coroutine
def upload():
	#when file's size greater than 4MB,using shard uploading 
	#after uploading successfully,return key name and file hash value

	response=yield bucket.res("key").put("./testfile") 
	print(response)

loop.run_sync(upload)
loop.close()
```

## Updating
	..............
  

