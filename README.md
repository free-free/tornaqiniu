## Description
> tornaqiniu is a qiniu cloud storage client for tornado

--------------

## Get Started:
```python
from tornaqiniu import QiniuClient

access_key="your qiniu access key"
secret_key="your qiniu secret key"
client=QiniuClient(access_key,secret_key,bucket="your bucket")
#get upload token
client.upload_token()

# get private url
client.private_url("resource key")

```
----

## Updating
	..............
  

