# -*- coding:utf-8 -*-
from tornado import gen
import os
from .common import Policy
from .resource import Resource, QiniuResourceLoader, QiniuResourceManager, QiniuResourceProcessor
from .utils import json_decode,json_encode,bytes_decode,bytes_encode,urlsafe_base64_encode


class Bucket(object):

    def __init__(self, host, auth, bucket_name, bucket_acp=0):
        r"""
        Args:
                auth:qiniu authentication object
                bucket_name:bucket name
                bucket_acp: bucket access property
                        0--->public bucket
                        1--->private bucket
        """
        self.__host = host
        self.__auth = auth
        self.__bucket_name = bucket_name
        self.__bucket_acp = bucket_acp
        self.__res_loader = QiniuResourceLoader(self.__auth)
        self.__res_manager = QiniuResourceManager(self.__auth)
        self.__res_processor = QiniuResourceProcessor(self.__auth)
        self.__policy = Policy()

    @property
    def acp(self):
        r"""
            Args:
                None
            Returns:
                bucket access property
        """
        return self.__bucket_acp

    @property
    def bucket_name(self):
        r"""
            Args:
                None
            Returns:
                bucket name
        """
        return self.__bucket_name

    @property
    def auth(self):
        r"""
            Args:
                None
            Returns:
                Auth object
        """
        return self.__auth

    def res(self, *res_key):
        r"""
            Args:
                res_key : resource key
            Returns:
                Resource Map object
        """
        return Resource(self, *res_key)

    def upload_token(self, key=None, bucket=None, expires=3600, policys=None):
        r"""
            Args: 
                key : resource key 
                bucket : resource bucket name
                expires : expire time,unit second
                policys : upload policy ,dict type or Policy type
            Returns:
                upload_token
        """
        bucket = bucket or self.__bucket_name
        assert bucket != None and bucket != "", "invalid bucket"
        if isinstance(policys, Policy):
            all_policys = policys.policys
        elif isinstance(policys, dict):
            all_policys = policys
        else:
            all_policys = self.__policy.policys
        return self.__auth.upload_token(bucket, key, expires, all_policys)

    def private_url(self, key, expires=3600, host=None):
        """create private resource url
        Args:
                key:resource key
                expires:url expires time
                host:resource host
        Returns:
                resource private url
        """
        return self.__res_loader.private_url(key, expires, host or self.__host)

    def public_url(self, key, host=None):
        """
        Args:
            key:resource key name
        Returns:
            resource public url
        """
        return self.__res_loader.public_url(key, host or self.__host)

    @gen.coroutine
    def put(self, key, filename, host="upload.qiniu.com", accept="json"):
        r"""
        Args:
            key : resource key name
            filename : upload file name
            host : upload host name
            accept : response type (json/xml)
        Returns:
            resource hash value and resource key name
        """
        filesize = os.path.getsize(filename)
        # when file size greater than 4 MB,using shard uploading
        if filesize > 4194304:
            response = yield self.__res_loader.shard_upload(key,\
                filename, self.bucket_name, host)
            return response
        else:
            response = yield self.__res_loader.single_upload(key,\
                filename, self.bucket_name, host, accept)
            if accept.lower() == 'json':
                if response:
                    return json_decode(bytes_decode(response.body))
            else:
                if response:
                    return bytes_decode(response.body)

    @gen.coroutine
    def stat(self, key, bucket=None):
        """get resource detail information
        Args:
                key:resource key
                bucket:bucket name,if bucket name is None,
                       self._bucket will replace it
        Returns:
                a dict for resource information
        """
        response = yield self.__res_manager.stat(key, bucket or self._bucket)
        return response

    @gen.coroutine
    def move(self, s_key, s_bucket, d_key, d_bucket):
        """ move resource to another bucket,it's a tornado coroutine
        Args:
                s_bucket:src bucket name
                s_key:src key name
                d_bucket:destination bucket name
                d_key:destination key name
        Returns:
            None
        """
        response = yield self.__res_manager.move(s_key, s_bucket, d_key, d_bucket)
        return response

    @gen.coroutine
    def copy(self, s_key, s_bucket, d_key, d_bucket):
        """ copy resource to another bucket,it's a tornaod coroutine
        Args:
                almost same with 'move(**)'
        Returns:
                None
        """
        response = yield self.__res_manager.copy(s_key, s_bucket, d_key, d_bucket)
        return response

    @gen.coroutine
    def delete(self, key, bucket=None):
        """delete a resource
        Args:
                key:resource key name
                bucket:bucket name,if bucket is None,self._bucket will replace it
        Returns
                None
        """
        response = yield self.__res_manager.delete(key, bucket or self.__bucket_name)
        return response

    @gen.coroutine
    def list(self, bucket=None, limit=1000, prefix="", delimiter="", marker=""):
        """list  resource detail information that meet requirements
        Args:
                refer to qiniu document
        Returns:
                a list of resource information
        """
        response = yield self.__res_manager.list(bucket or self._bucket, limit, prefix, delimiter, marker)
        return response

    @gen.coroutine
    def fetch_store(self, fetch_url, key=None, bucket=None):
        """fecth resource of 'fecth_url' ,then save it to 'bucket'
        Args:
                fetch_url:fetch url
                key:resource saving key name
                bucket:resource saving bucket name
        Returns:
                None
        """
        response = yield self.__res_manager.fetch_store(fetch_url, key, bucket or self._bucket)
        return response

    @gen.coroutine
    def batch(self, *opers):
        """ execute multi resource management operations
        Args:
                *opers:opertions
        Returns:
                None
        """
        response = yield self.__res_manager.batch(*opers)
        return response

    @gen.coroutine
    def prefetch(self, key, bucket=None):
        r"""
            Args:
                key : resource key
                bucket : bucket name
            Returns:
                json type
        """
        response = yield self.__res_manager.prefetch(key, bucket or self._bucket)
        return response

    @gen.coroutine
    def prefop(self, persistent_id):
        r"""
            Args:
                persistent_id : persistent_id
            Returns:
                json 
        """
        response = yield self.__res_processor.prefop(persistent_id)
        return response

    def persistent(self, key, notify_url, fops=None, force=1, pipeline=None):
        r"""
            Args:
                key : resource key
                notify_url : callback url after procession done
                fops : operations 
                force : 1 or 9
                pipeline : process pipeline
            Returns:
                _PersistentWrapper object that defined in _PersistentWrapper
         """
        return self.__res_processor.persistent(key, notify_url, self.__bucket_name, fops, force, pipeline)

    def image_views(self, url, mode, width=None, height=None, **kwargs):
        r"""
            Args:
                url : resource url
                mode : imageView2 mode 
                width : image width
                height : image height
                kwargs : other args for imageView2 interface 
                the details refer to:http://developer.qiniu.com/code/v6/api/kodo-api/image/imageview2.html
            Returns:
                resource imageview2 url
        """
        return self.__res_processor.image_view2(url,
                                                mode,
                                                width,
                                                height,
                                                **kwargs
                                                )

    def image_watermark(self, origin_url, water_img_url, **kwargs):
        r"""
            Args:
                origin_url : image url that need to watermark
                water_img_url : water image url
                kwargs : other optional args for image_watermark interface
                the details refer to :
                http://developer.qiniu.com/code/v6/api/kodo-api/image/watermark.html
           Returns:
                resource image watermark url
        """
        return self.__res_processor.image_watermark(origin_url,
                                                    water_img_url,
                                                    **kwargs
                                                    )

    def text_watermark(self, origin_url, text, **kwargs):
        r"""
            Args:
                origin_url : image url that need to watermark
                text : text for watermark
                kwargs : optional args for text_watermark interface
                the details refer to :
                http://developer.qiniu.com/code/v6/api/kodo-api/image/watermark.html
            Returns:
                 retource text watermark url
        """
        return self.__res_processor.text_watermark(origin_url,
                                                   text,
                                                   **kwargs
                                                   )

    @gen.coroutine
    def imageinfo(self, origin_url):
        r"""
           Args:
               origin_url : image url
           Returns:
                json type for image  information 
        """
        response = yield self.__res_processor.get_imageinfo(origin_url)
        return response

    @gen.coroutine
    def imageexif(self, origin_url):
        r"""
            Args:
                origin_url : image url
            Returns:
                json type for image exif 
        """
        response = yield self.__res_processor.get_imageexif(origin_url)
        return response

    @gen.coroutine
    def imageave(self, origin_url):
        r"""
            Args: 
                origin_url : image url
            Returns:
                 string type for image ave
        """
        response = yield self.__res_processor.get_imageave(origin_url)
        return response

    @gen.coroutine
    def avinfo(self, av_url):
        r"""
             Args:
                 av_url : audio/vedio url
             Returns:
                 json type for audio/vedio information
        """
        response = yield self.__res_processor.get_avinfo(av_url)
        return response
