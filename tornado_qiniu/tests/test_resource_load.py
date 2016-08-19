#-*- coding:utf-8 -*-

from tornado.testing import AsyncTestCase
from tornado.testing import gen_test
import tornado.testing
from tornado import ioloop
from tornado import gen
from tornado_qiniu import QiniuClient,Policy
import time
import os
import tempfile
ACK = os.getenv("ACCESS_KEY")
SEK = os.getenv("SECRET_KEY")
DOMAIN = os.getenv("DOMAIN")
BUCKET = os.getenv("BUCKET")

def make_tmpfile(size):
    tname = tempfile.mktemp()
    with open(tname,'w+b') as f:
        f.seek(size-1)
        f.write(b'0')
        f.close()
    return tname

class TestResourceLoad(AsyncTestCase):

    client = QiniuClient(ACK, SEK, DOMAIN)

    def test_private_url(self):
        bucket = self.client.bucket(BUCKET, bucket_acp=1)
        purl = bucket.res('dummy_key').url()
        assert  purl != None

    def test_public_url(self):
        bucket = self.client.bucket(BUCKET, bucket_acp=0)
        purl = bucket.res("dummy_key").url()
        assert purl != None

    def test_multi_url(self):
        bucket = self.client.bucket(BUCKET)
        urls = bucket.res("dummy_key1","dummy_key2").url()
        assert len(urls) == 2

    @gen_test(timeout=60)
    def test_resource_upload(self):
        tname = make_tmpfile(1024*1024)
        bucket = self.client.bucket(BUCKET, bucket_acp=1)
        response = yield bucket.res('dummy_file').put(tname)
        assert "hash" in response

    @gen_test(timeout=60)
    def test_resource_download(self):
        bucket = self.client.bucket(BUCKET, bucket_acp=1)
        response = yield bucket.res("image/python.jpg").get('hello.jpg')
        assert response != None 
    
    @gen_test(timeout=60)
    def test_multi_resource_download(self):
        bucket =  self.client.bucket(BUCKET,bucket_acp=1)
        response = yield bucket.res("image/python.jpg","image/java.jpg").get()
        assert len(response) == 2

    def test_upload_token(self):
        bucket = self.client.bucket(BUCKET, bucket_acp=1)
        upload_token = bucket.upload_token()
        assert upload_token != None


class TestPolicy(AsyncTestCase):
    
    def test_deadline(self):
        policy = Policy()
        dt = time.time()
        policy.deadline = dt
        assert 'deadline' in policy.policys

    def test_scope(self):   
        policy = Policy()
        policy.scope = BUCKET
        #assert "scope" in policy.policys 
        assert policy["scope"] == BUCKET

    def test_persistent_ops(self):
        policy = Policy()
        policy.persistent_ops = "dummy_ops"
        assert "persistentOps" in policy.policys
        assert policy['persistent_ops'] == 'dummy_ops'

    def test_save_key(self):
        policy = Policy()
        policy.save_key = "dummy_key"
        assert "saveKey" in policy.policys
        assert policy['save_key'] == "dummy_key"
   
    def test_callback_url(self):
        policy = Policy()
        policy.callback_url = "http://localhost/callback/1"
        policy.callback_url = "http://localhost/callback/2"
        assert "callbackUrl" in policy.policys
        assert policy['callback_url'] == "http://localhost/callback/1;http://localhost/callback/2"
   
    def test_delete_all_policys(self):
        policy = Policy()
        policy.scope = BUCKET
        policy.deadline = time.time()
        policy.delete_all_policys()
        assert not policy.policys
    
if __name__ == '__main__':
	tornado.testing.main()




