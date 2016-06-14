## Description
	tornaqiniu is a qiniu cloud storage client for tornado

## Get Started:
### 1.Resource Upload and Download
```python
from tornado imoprt gen,ioloop
from tornaqiniu import QiniuClient

access_key="your qiniu access key"
secret_key="your qiniu secret key"
bucket_name="your bucket name"
domain="your domain"
bucket_acp=0   #bucket access property,1 ===>private bucket,0===>public bucket

client=QiniuClient(access_key,secret_key,domain)

#get a bucket instance
bucket=client.bucket(bucket_name,bucket_acp=1)

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
### 2.Resource Management
```python

from tornado import gen,ioloop
from tornaqiniu import QiniuClient

access_key="your qiniu access key"
secret_key="your qiniu secret key"
bucket_name="your bucket name"
domain="your domain"
bucket_acp=0   #bucket access property,1 ===>private bucket,0===>public bucket

client=QiniuClient(access_key,secret_key,domain)
bucket=client.bucket(bucket_name,bucket_acp=bucket_acp)

loop=ioloop.IOLoop.current()

#single resource management
@gen.coroutine
def single_resource_manage():
	#resource state
	state=yield bucket.res('key').stat()

	#resource deleting
	yield bucket.res('key').delete()
	
	#resource moving
	yield bucket.res('src_key').moveto('dest_key','dest_bucket')
	
	#resource coping
	yield bucket.res('src_key').copyto('dest_key','dest_bucket')
loop.run_sync(single_resource_manage)
	

#multi resource management
@gen.coroutine
def multi_resource_manage():
	#multi resource state
	state=yield bucket.res('key1','key2','key3').multi_stat()
	
	#multi resource deleting
	yield bucket.res('key1','key2','key3').multi_delete()
	
	#multi resource coping
	yield bucket.res(*['key1','key2']).multi_copyto(['dest_key1','dest_key2'],'dest_bucket')
	
	#multi resource moving
	yield bucket.res('key1','key2').multi_moveto(['dest_key1','dest_key2'],'dest_bucket')
		

loop.run_sync(multi_resource_manage)

# resource management bacth operation
@gen.coroutine
def bacth_ops():
	#get batch instance
	batch=bucket.res().batch()
	batch.stat('keyname1')	
	batch.delete('keyname2')
	yield batch.execute()

```
## Updating
	..............
  

