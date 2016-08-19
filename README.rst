qiniu storage asynchronous sdk for tornado
=================================================

.. image:: https://img.shields.io/github/license/mashape/apistatus.svg
  :target: LICENSE


Installation
---------------

.. code-block:: bash

    $ python3.x setup.py install


or

.. code-block:: bash
    
    $ pip3.x install tornado_qiniu


Environment
-------------------

.. list-table::
   :widths: 50 50
   :header-rows: 1

   * - tornado_qiniu version 
     - python version
   * - 1.0
     - 3.4,3.5


Quick Start
---------------------

Resource Upload and Download
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from tornado import gen,ioloop
    from tornado_qiniu import QiniuClient

    access_key = "your qiniu access key"
    secret_key = "your qiniu secret key"
    bucket_name = "your bucket name"
    domain = "your domain"
    bucket_acp = 0   #bucket access property,1 ===>private bucket,0===>public bucket

    client = QiniuClient(access_key, secret_key, domain)
    loop = ioloop.IOLoop.current()

    #get a bucket instance
    bucket = client.bucket(bucket_name, bucket_acp=1)

    #get bucket upload token
    bucket.upload_token()

    # get resource url
    bucket.res("resource_key").url()
    bucket.res('key1','key2').url()

    # download resource
    @gen.coroutine
    def get_resource():
        response = yield bucket.res("resource_key").get() #return   saved name
        # get multi resource 
        response = yield bucket.res('key1','key2').get()  #return a list of the  saved  name
    loop.run_sync(get_resource)

    # upload resource
    @gen.coroutine
    def upload():
        #when file's size greater than 4MB,using shard uploading 
        #after uploading successfully,return key name and file hash value
        response = yield bucket.res("key").put("./testfile") #return resource hash value,and key

    loop.run_sync(upload)
    loop.close()


Resource Management
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from tornado import gen,ioloop
    from tornado_qiniu import QiniuClient

    access_key = "your qiniu access key"
    secret_key = "your qiniu secret key"
    bucket_name = "your bucket name"
    domain="your domain"
    bucket_acp = 0   #bucket access property,1 ===>private bucket,0===>public bucket

    client = QiniuClient(access_key,secret_key,domain)
    bucket = client.bucket(bucket_name,bucket_acp=bucket_acp)
    loop = ioloop.IOLoop.current()

    #single resource management
    @gen.coroutine
    def single_resource_manage():
        #resource state
        state = yield bucket.res('key').stat()

        #resource deleting
        yield bucket.res('key').delete()
	
        #resource moving
        yield bucket.res('src_key').moveto('dest_key', 'dest_bucket')
	
        #resource coping
        yield bucket.res('src_key').copyto('dest_key', 'dest_bucket')
    loop.run_sync(single_resource_manage)
	
    #multi resource management
    @gen.coroutine
    def multi_resource_manage():
        #multi resource state
        state = yield bucket.res('key1', 'key2', 'key3').multi_stat()
	
        #multi resource deleting
        yield bucket.res('key1', 'key2', 'key3').multi_delete()
	
        #multi resource coping
        yield bucket.res(*['key1', 'key2']).multi_copyto(['dest_key1', 'dest_key2'],'dest_bucket')
	
        #multi resource moving
        yield bucket.res('key1', 'key2').multi_moveto(['dest_key1', 'dest_key2'],'dest_bucket')
    loop.run_sync(multi_resource_manage)

    # resource management batch operation
    @gen.coroutine
    def batch_ops():
        #get batch instance
        batch = bucket.res().batch()
        batch.stat('keyname1')	
        batch.delete('keyname2')
        #execute batch
        yield batch.execute()
	
        #multi resource batch operation
        batch = bucket.res('key1', 'key2').batch()
        batch.multi_stat()
        batch.multi_copy(['dest_key1', 'dest_key2'], 'dest_bucket')
        batch.multi_move(['dest_key1', 'dest_key2'], 'dest_bucket')

        #list all resources in current bucket
        batch.list()
        #execute batch ,return json format data
        yield bacth.execute()
    loop.run_sync(batch_ops)


Resource Process
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from tornado import gen,ioloop
    from tornado_qiniu import QiniuClient

    access_key = "your qiniu access key"
    secret_key = "your qiniu secret key"
    bucket_name = "your bucket name"
    domain="your domain"
    bucket_acp = 0   #bucket access property,1 ===>private bucket,0===>public bucket

    client = QiniuClient(access_key,secret_key,domain)
    bucket = client.bucket(bucket_name,bucket_acp=bucket_acp)
    loop = ioloop.IOLoop.current()

    # get resource info
    @gen.coroutine
    def get_info():
    
        # get image info
        imginfo = yield bucket.res("dummy_img_key").imageinfo().get()
    
        # get image ave
        imgave = yield bucket.res("dummy_img_key").imageave().get()
    
        # get image exif
        imgexif = yield bucket.res("dummy_img_key").imageexif().get()
    
    loop.run_sync(get_info)

    # resource fops
    @gen.coroutine
    def resource_fops():
        # resource qrcode url
        qrcodeurl = bucket.res("dummy_img_key").fops().qrcode().url()
    
        # get resource qrcode img
        qrcodeimg = yield bucket.res("dummy_img_key").fops().qrcode().get()

        # resource text_watermark
        text_watermark_url = bucket.res("dummy_img_key").fops().text_watermark("dummy").url()
        text_watermark_img = yield bucket.res("dummy_img_key").fops().text_watermark("dummy").get()

        #  resource image watermark
        img_url = bucket.res("water_img").url()
        watered_img_url = bucket.res("dummy_img_key").fops().image_watermark(img_url).url()
        waterd_img = yield bucket.res("dummy_img_key").fops().image_watermark(img_url).get()
    
        # resource fops saveas
        saveas_url = bucket.res("dummy_key").fops().text_watermark("dummy").saveas("dummy_watermark").url()
        yield bucket.res("dummy_key").fops().text_watermark("dummy").saveas("dummy_watermark").get()

        # resource fops persistent
   
        # audio/vedio slice operation, the detail args refer to:
        # http://developer.qiniu.com/code/v6/api/dora-api/av/segtime.html

        yield bucket.res("dummy_av").fops().avthumb_slice(no_domain=1).persistent()
    
        # audio/vedio transcoding operation,the detail args refer to:
        # http://developer.qiniu.com/code/v6/api/dora-api/av/avthumb.html
        yield bucket.res("dummy_av").fops().avthumb_transcoding("mp3").persistent()
   
        # audio/vedio concat operation,the detail args refer to :
        # http://developer.qiniu.com/code/v6/api/dora-api/av/avconcat.html
        yield bucket.res("dummy_av").fops().avconcat(mode=2, frmt="mp4", url1="http://**",url2="http://**").persistent()
    
        # audio/vedio vframe operation ,the detail args refer to:
        # http://developer.qiniu.com/code/v6/api/dora-api/av/vframe.html
        yield bucket.res("dummy_av").fops().vframe("jpg", 200, w=1000, h=3030).persistent()
    
        # get audio/vedio information
        avinfo = yield bucket.res("dummy_av").avinfo().get()
        avinfo_url = bucket.res("dummy_av").avinfo().url()

        # prefop interface
        response = yield bucket.res("key1").prefop("persistent_id")
    

License
-----------------

`MIT License <LICENSE>`_
