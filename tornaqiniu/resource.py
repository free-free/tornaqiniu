#-*- coding:utf-8 -*-

import logging
logging.basicConfig(level=logging.ERROR)
from tornado import gen, httpclient
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
import threading
import hmac
import hashlib
import base64
from datetime import datetime
import uuid
import json
from .errors import *
from .utils import *
from . import PUT_POLICY
from .common import Auth
from .interface import QiniuInterface
import os

##################################################################
#
# Qiniu Resource Loader that's responsible for uploading resource to
# bucket or downloading resource from bucket and generate download url
#
#
#################################################################


class QiniuResourceLoader(object):

    def __init__(self, auth):
        self._auth = auth

    def _gen_private_url(self, key, host, expires=3600):
        assert host != None and host != "", "download host can' be empty"
        if not host.startswith("http://"):
            host = "http://" + host
        download_url = host + '/' + key
        token = self._auth.download_token(download_url, expires=expires)
        download_url += '?e=' + \
            str(int(datetime.timestamp(datetime.now())) + expires)
        download_url += "&token=" + token
        return download_url

    def private_url(self, key, host, expires=3600):
        r"""
            generate one private url
            @Args:
                key:resource key,'str' type,
                expires:'int' type,units:'s',
                host:resource host name
         """
        return self._gen_private_url(key, expires, host)

    @gen.coroutine
    def single_upload(self, key, filename, bucket, host="upload.qiniu.com", accept="json"):
        upload_token = self._auth.upload_token(bucket, key)
        fields = {}
        if key:
            fields['key'] = key
        fields['token'] = upload_token
        # fields['crc32']='1'
        fields['accept'] = 'application/' + accept
        files = {}
        files['file'] = filename
        content_type, body = multipart_formdata(fields, files)
        headers = {}
        headers['Content-Type'] = content_type
        headers['Content-Length'] = str(len(body))
        headers['Host'] = host
        response = yield send_async_request("http://" + host + '/', headers=headers, method="POST", body=body)
        return response

    @gen.coroutine
    def shard_upload(self, key, filename, bucket, host="upload.qiniu.com"):
        print("beging uplod")
        # upload token
        upload_token = self._auth.upload_token(bucket, key)
        # file size
        file_size = os.path.getsize(filename)
        # uploding block info tmp file
        path, name = os.path.split(filename)
        name = '.' + name.split('.')[0] + '_' + \
                                str(int(os.path.getmtime(filename)))
        tmp_file = path + name
        # default upload block size,unit: byte
        BLOCK_SIZE = 4194304  # 4MB
        # block number of each uploading
        ep_blk_num = 3
        # last ctx information list of all block
        ctxlist = []
        # total block number of file
        total_block_num = (file_size // BLOCK_SIZE)
        if (file_size % BLOCK_SIZE) > 0:
            total_block_num += 1

        blks = {'blk_meta': {}, 'blk_ctx': [], 'blk_num': total_block_num}
        # check uploading tmp file's existen,if exists,
        # reupload failed blocks according to tmp file
        if os.path.exists(tmp_file) and os.path.getsize(tmp_file) == 0:
            os.remove(tmp_file)
        if os.path.exists(tmp_file):
            # get block meta data from tmp file
            with open(tmp_file, 'r') as f:
                blks = json.load(f)
        else:
            # build  block meta dat
            for bid in range(0, total_block_num):
                blk_meta = {}
                blk_meta['bid'] = bid
                blk_meta['bsp'] = (bid << 22)
                if bid == (total_block_num - 1) and (file_size % BLOCK_SIZE) > 0:
                    blk_meta['bsize'] = file_size % BLOCK_SIZE
                else:
                    blk_meta['bsize'] = (1 << 22)
                blks['blk_meta'][bid] = blk_meta
            with open(tmp_file,'w') as f:
                json.dump(blks,f)                
        blks_id = set(list(blks['blk_meta'].keys()))
	# get last upload ctx list
        ctxlist=blks['blk_ctx']
        print(blks_id)
        with ThreadPoolExecutor(max_workers=8) as executor:
            with open(tmp_file, 'r+') as tmp_f, open(filename, 'r+b') as data_f:
                while len(blks_id) > 0:
                    blocks = []
                    if len(blks_id)<ep_blk_num:
                        ep_blk_num=len(blks_id)
                    for i in range(0, ep_blk_num):
                        bid = blks_id.pop()
                        blk_meta = blks['blk_meta'].get(bid)
                        data_f.seek(blk_meta['bsp'])
                        bdata = data_f.read(blk_meta['bsize'])
                        blocks.append({'bid': bid,
                                       'bmeta': blk_meta,
                                       'bdata': bdata,
                                       'handler': self.__blk_upload_finish_handler(bid, tmp_f),
                                     })
                    upload_coroutines = [self._block_upload(
                        executor, block, upload_token, host) for block in blocks]
                    responses = yield upload_coroutines
                    for response in responses:
                        if not response:
                            continue
                        ctxlist.append(response)
                    blocks = []
        if len(ctxlist) != blks['blk_num']:
            logging.error("===> upload file '{0}' failed".format(filename))
            with open(tmp_file, 'r+') as tmp_f:
                blks = json.load(tmp_f)
                tmp_f.truncate(0)
                tmp_f.seek(0)
                blks['blk_ctx'] = ctxlist
                json.dump(blks, tmp_f)
            return None
        os.remove(tmp_file)
        #sort ctxlist by block id
        ctxlist = sorted(ctxlist, key=lambda ctx:int(ctx[0]))
        #get ctx
        ctxlist = list(map(lambda ctx:ctx[1],ctxlist))
        # merge all block info origin  file
        response = yield self._mkfile(key, file_size, ctxlist, upload_token, host)
        return response

    def __blk_upload_finish_handler(self, bid, file_obj):
        r'''
            when block uploading failed ,return a handler to store failed block's information
        '''
        def handler():
            r"""
                 [{"bid":bid},{},...]
            """
            with threading.Lock():
                try:
                    blks_info = json.load(file_obj)
                    file_obj.truncate(0)
                    file_obj.seek(0) 
	   	    # delete block meta data in tmp tile
                    del blks_info['blk_meta'][str(bid)]
                    print(blks_info)
                    json.dump(blks_info, file_obj)
                    file_obj.seek(0)
                except Exception:
                    print("error in hndle")
        return handler

    @gen.coroutine
    def _block_upload(self, executor, block, upload_token, host):
        # chunk size ,default if 256 KB
        CHUNK_SIZE = 262144  # 256KB
        # max times of making block and uploading chunk
        MAX_TIMES = 3
        # block size
        bsize = block['bmeta'].get('bsize')
	# block id
        bid = block.get('bid')
        # block data
        bdata = block.get('bdata')
        # start offset in chunk for each bput
        start_point = 0
        # end offset in chunk for each bput
        end_point = CHUNK_SIZE
        #  error counter
        error_cnt = 0
        # make block flag
        mkblk_flag = True
        # block size smaller than single chunk size,set end_point's value equal
        # to block size
        if (bsize - start_point) < CHUNK_SIZE:
            end_point = bsize
        # slice first chunk
        chunk = bdata[start_point:end_point]
        # make a block and upload first chunk
        while mkblk_flag:
            print("mking block %s" % bid)
            future = executor.submit(
                self._mkblock, chunk, upload_token, host, bsize)
            try:
                response = yield future
            except Exception as e:
                error_cnt += 1
                # if block uploading failed,raise BlockUploadError exception
                if error_cnt > MAX_TIMES:
                     logging.error("Making Block {0} Failed!".format(bid))
                     return None
                logging.error(
                    "Making Block {0} Error {1} ,remake block !".format(bid, e))
            else:
                # make block successfully,update start_point and end_point
                start_point = end_point
                end_point += CHUNK_SIZE
                # end loop
                mkblk_flag = False
        error_cnt = 0
        # upload left chunk
        while start_point < bsize:
            print("bput of block %s" % bid)
            if (bsize - start_point) < CHUNK_SIZE:
                end_point = bsize
            chunk = bdata[start_point:end_point]
            future = executor.submit(self._bput, chunk, response['ctx'], response[
                                     'offset'], upload_token, host)
            try:
                response = yield future
            except Exception as e:
                error_cnt += 1
                if error_cnt > MAX_TIMES:
                    logging.error("Uploading Block {0} Failed!".format(bid))
                    return None
                logging.error(
                    "Uploading Chunk Of The Block {0} Error: {1} , reupload chunk !".format(bid, e))
            else:
                error_cnt=0
                start_point = end_point
                end_point += CHUNK_SIZE
        # upload block successfully,call block uploading finished handler
        handler=block['handler']
        handler()
        return (bid, response.get('ctx'))

    def _mkblock(self, first_chunk, upload_token, host, block_size=4194304):
        headers={}
        headers['Host']=host
        headers['Content-Type']='application/octet-stream'
        headers['Content-Length']=len(first_chunk)
        headers['Authorization']='UpToken ' + upload_token
        response=send_sync_request("http://" + host + "/mkblk/" + str(
            block_size), method="POST", headers=headers, body=first_chunk)
        if response:
            return json_decode(bytes_decode(response.body))

    def _bput(self, chunk, ctx, offset, upload_token, host):
        headers={}
        headers['Host']=host
        headers['Content-Type']='application/octet-stream'
        headers['Content-Length']=len(chunk)
        headers['Authorization']="UpToken " + upload_token
        response=send_sync_request("http://" + host + "/bput/" + str(ctx) + \
            '/' + str(offset), method="POST", headers=headers, body=chunk)
        if response:
            return json_decode(bytes_decode(response.body))

    @gen.coroutine
    def _mkfile(self, key, filesize, ctxlist, upload_token, host):
        ctx=','.join(ctxlist)
        headers={}
        headers['Host']=host
        headers['Content-Type']='text/plain'
        headers['Content-Length']=len(ctx)
        headers['Authorization']="UpToken " + upload_token
        url="http://" + host + '/mkfile/' + str(filesize)
        if key:
            encoded_key=bytes_decode(urlsafe_base64_encode(key))
            url += '/key/' + str(encoded_key)
        response=yield send_async_request(url, method="POST", headers=headers, body=ctx)
        if response:
            return json_decode(bytes_decode(response.body))

    def private_urls(self, keys, host, expires=3600, key_name=None):
        """
            generate multi private urls at the same time
            @Args:
                keys:resource keys ,'list','dict' or  'tuple' type,
                expires:int type,units:'s',
                host:resource host name,
                key_name:when  'keys' type  is 'dict',your must point out key name in 'keys'
            @Return:
                download_urls: 'list' typw
        """
        download_urls=[]
        if isinstance(keys, (list, tuple)):
            if key_name:
                for key in keys:
                    download_urls.append(self._gen_private_url(key[key_name]), expires, host)
            else:
                for key in keys:
                    download_urls.append(self._gen_private_url(key, expires, host))
        else:
            pass
            return download_urls

    def _gen_public_url(self, key, host):
        assert host != None and host != "", " host can't be empty"
        if not host.startswith("http://"):
            host="http://" + host
        download_url=host + '/' + key
        return download_url

    def public_url(self, key, host):
        r"""
            generate public url
            @Args:
                key:resource key,'str' type,
                host:resource host name
        """
        return self._gen_public_url(key, host)

    def public_urls(self, keys, host, key_name=None):
        r"""
            generate multi public url
            the parameters difinition is same with 'private_urls'
        """
        download_urls=[]
        if isinstance(keys, (tuple, list)):
            if key_name:
                for key in keys:
                    download_urls.append(self._gen_public_url(key[key_name], host))
            else:
                for key in keys:
                    download_urls.append(self._gen_public_url(key, host))
        else:
            pass
        return download_urls


##########################################################################
#
#
# Qiniu Resource manager that's responsible for bucket resouce management ,
# like 'delete','copy','move' and so on
#
#
#
##############################################################################
class QiniuResourceManager(object):
	def __init__(self, auth):
		self._auth=auth
	@gen.coroutine
	def _send_manage_request(self, url_path, host="rs.qiniu.com", body=None, method="POST"):
		full_host="http://" + host
		url=full_host + url_path
		headers={
			"Authorization": self._auth.callback_verify_header(url_path, body),
			"Host": host
		}
		response=yield send_async_request(url, headers=headers, method=method, body=body)
		if response:
			return bytes_decode(response.body)
	@gen.coroutine
	def stat(self, key, bucket):
		host, interface=QiniuInterface.stat(key, bucket)
		response=yield self._send_manage_request(interface, host=host)
		return response
	@gen.coroutine
	def move(self, src_key, src_bucket, dest_key, dest_bucket):
		host, interface=QiniuInterface.move(
		    src_key, src_bucket, dest_key, dest_bucket)
		response=yield self._send_manage_request(interface, host=host, method="POST")
		return response
	@gen.coroutine
	def modify_mime(self, bucket, key, mine_type):
		pass

	@gen.coroutine
	def copy(self, src_key, src_bucket, dest_key, dest_bucket):
		host, interface=QiniuInterface.copy(
		    src_key, src_bucket, dest_key, dest_bucket)
		response=yield self._send_manage_request(interface, host=host, method="POST")
		return response
	@gen.coroutine
	def delete(self, key, bucket):
		host, interface=QiniuInterface.delete(key, bucket)
		response=yield self._send_manage_request(interface, host=host, method="POST")
		return response
	@gen.coroutine
	def list(self, bucket, limit=1000, prefix="", delimiter="", marker=""):
		host, interface=QiniuInterface.list(bucket, limit, prefix, delimiter, marker)
		response=yield self._send_manage_request(interface, host="rsf.qbox.me", method="POST")
		return response
	@gen.coroutine
	def fetch_store(self, fetch_url, bucket, key=None):
		host, interface=QiniuInterface.fetch_store(fetch_url, key, bucket)
		response=yield self._send_manage_request(interface, host=host, method="POST")
		return response
	@gen.coroutine
	def batch(self, *opers):
		opers=list(map(lambda op: 'op=' + op, opers))
		opers_str="&".join(opers)
		response=yield self._send_manage_request('/batch', method="POST", body=opers_str)
		return response
	@gen.coroutine
	def prefetch(self, key, bucket):
		host, interface=QiniuInterface.prefetch(key, bucket)
		response=yield self._send_manage_request(interface, method="POST", host=host)
		return response


##########################################################################
#
#
# Qiniu resource processor that's responsible for bucket resource procession
# like 'imageView2','QRCode','Audio/Vedio thumb'
#
##########################################################################

class QiniuImageProcessMixin:
	def image_view2(self, url, mode, width=None, height=None, **kwargs):
		host, interface=QiniuInterface.image_view2(mode, width, height, **kwargs)
		resulted_url=url
		if url.find("?") >= 0:
			resulted_url += "&" + interface
		else:
			resulted_url += "?" + interface
		return resulted_url
	def image_watermark(self, origin_url, water_image_url, **kwargs):
		host, interface=QiniuInterface.image_watermark(water_image_url, **kwargs)
		resulted_url=origin_url
		if origin_url.find("?") >= 0:
			resulted_url += '&' + interface
		else:
			resulted_url += '?' + interface
		return resulted_url

	def text_watermark(self, origin_url, text, **kwargs):
		host, interface=self.text_watermark_interface(text, **kwargs)
		resulted_url=origin_url
		if origin_url.find("?") >= 0:
			resulted_url += '&' + interface
		else:
			resulted_url += "?" + interface
		return resulted_url
	def multi_watermark(self, origin_url, *args):
		"""
			multi watermark parameters are too much,
			so i decided to implement it at the next time.
		"""
		pass
	def imageinfo_url(self, origin_url):
		if origin_url.find("?") >= 0:
			return origin_url + "&imageInfo"
		else:
			return origin_url + "?imageInfo"
	def multi_imageinfo_url(self, urls, key_name=None):
		if isinstance(urls, (list, tuple)):
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
	def get_imageinfo(self, origin_url):
		url=self.imageinfo_url(origin_url)
		response=yield self.send_async_request(url)
		if response:
			return json_decode(response)
	def imageexif_url(self, origin_url):
		if origin_url.find("?") >= 0:
			return origin_url + '&exif'
		else:
			return origin_url + '?exif'
	def multi_imageexif_url(self, urls, key_name=None):
		if isinstance(urls, (list, tuple)):
			exif_urls=[]
			if key_name:
				for url in urls:
					exif_urls.append(self.imageexif_url(url[key_name]))
			else:
				for url in urls:
					exif_urls.append(self.imageexif_url(url))
			return exif_urls
	@gen.coroutine
	def get_imageexif(self, origin_url):
		url=self.imageexif_url(origin_url)
		response=yield self.send_async_request(url)
		return response
	def imageave_url(self, origin_url):
		if origin_url.find("?") >= 0:
			return origin_url + '&imageAve'
		else:
			return origin_url + '?imageAve'
	def multi_imageave_url(self, urls, key_name):
		if isinstance(urls, (list, tuple)):
			ave_urls=[]
			if key_name:
				for url in urls:
					ave_urls.append(self.imageave_url(url[key_name]))
			else:
				for url in urls:
					ave_urls.append(self.iamgeave_url(url))
			return ave_urls
	@gen.coroutine
	def get_imageave(self, origin_url):
		url=self.imageave_url(origin_url)
		response=yield self.send_async_request(url)
		if response:
			return json_decode(response).get("RGB")

class QiniuAVProcessMixin:
	def avinfo_url(self, av_url):
		if av_url.find("?") >= 0:
			return av_url + "&avinfo"
		else:
			return av_url + "?avinfo"
	@gen.coroutine
	def get_avinfo(self, av_url):
		avinfo_url=self.avinfo_url(av_url)
		response=yield self.send_async_request(avinfo_url)
		if response:
			return json_decode(response)
		return None


class _PersistentWrapper(object):
	"""
		make persistent operation 'pipeline' like executing
	"""
	def __init__(self, client_obj, key, fops, notify_url, bucket, force, pipeline):
		self.__client=client_obj
		self.__key=key
		self.__fops=[]
		self.__fops.extend(fops or "")
		self.__notify_url=notify_url
		self.__bucket=bucket or self.__client._bucket
		self.__force=force
		self.__pipeline=pipeline
	@gen.coroutine
	def execute(self):
		assert self.__bucket, "bucket can't be none"
		assert len(self.__fops) > 0, "fops can't be none"
		all_fops=";".join(self.__fops)
		body=urlencode({
			'bucket': self.__bucket,
			'key': self.__key,
			'fops': self.__fops,
			'notifyURL': self.__notify_url,
			'pipeline': self.__pipeline or "",
			'force': self.__force
		})
		response=yield self.__client._send_persistent_request('/pfop/', body=body, method="POST")
		if response:
			return json_decode(response)
		return None
	def add_fops(self, ops):
		self.__fops.append(ops)
	def add_multi_fops(self, ops_list):
		self.__fops.extend(list(ops_lsit))
	def set_pipeline(self, pipeline):
		self.__pipeline=pipeline
	def set_notify_url(self, url):
		self.__notify_url=url
	def set_force(self, force):
		if int(force) > 0:
			self.__force=1
		else:
			self.__force=0
	def set_key(self, key):
		self.__key=key
	def set_bucket(self, bucket):
		self.__bucket=bucket


class QiniuResourceProcessor(QiniuAVProcessMixin,
			   QiniuImageProcessMixin):
	def __init__(self, auth):
		self._auth=auth
	def qrcode_url(self, url, mode=0, level='L'):
		resulted_url=url
		interface=QiniuInterface.qrcode(mode, level)
		if url.find("?") >= 0:
			resulted_url += '&' + interface
		else:
			resulted_url += '?' + interface
		return resulted_url
	@gen.coroutine
	def get_qrcode(self, url, file_name=None, mode=0, level=1):
		url=self.qrcode_url(url, mode, level)
		response=yield send_async_request(url)
		response_type=response.headers.get("Content-Type").rsplit('/', 1)[1]
		if response:
			if not file_name:
				uid=uuid.uuid4().hex
				file_name=uuid + "." + response_type
			mkdir_recursive(os.path.dirname(file_name))
			with open(file_name, "w+b") as f:
				f.write(response.buffer.read())
			return file_name
		return None
	@gen.coroutine
	def _send_persistent_request(self, url_path, host="api.qiniu.com", body=None, method=None):
		url="http://" + host + url_path
		headers={}
		headers['Authorization']=self._auth.authorization(url_path, body)
		headers['Host']=host
		response=yield send_async_request(url, headers=headers, method=method or "POST", body=body)
		return bytes_decode(response.body)
	def persistent(self, key, notify_url, bucket=None, fops=None, force=1, pipeline=None):
		"""
			Usage:

				client=QiniuClient('access_key','secret_key',bucket='your bucket')
				persistent.add_fops(client.text_watermark_interface("hello"))
				yield persistent.execute()


		"""
		return _PersistentWrapper(self, key, fops, notify_url, bucket, force, pipeline)
	@gen.coroutine
	def prefop(self, persistent_id):
		interface=QiniuInterface.prefop(persistent_id)
		response=yield self._send_persistent_request(interface, method="GET")
		if response:
			return json_decode(response)



class Fops(object):
	def __init__(self, fops=None, res=None):
		self.__res=res
		self.__fops=fops or []
		if isinstance(fops, (list, tuple)):
			self.__fops.extend(list(fops))
	def __add_fops_to_resource(self, fops):
		if self.__res:
			self.__res._vpipe["fops"].append(fops)
	def image_watermark(self, water_image_url, **kwargs):
		fops=QiniuInterface.image_watermark(water_image_url, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def text_watermark(self, text, **kwargs):
		fops=QiniuInterface.text_watermark(text, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def image_view2(self, mode, width=None, height=None, **kwargs):
		fops=QiniuInterface.image_view2(mode, width, height, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def qrcode(self, mode=0, level='L'):
		fops=QiniuInterface.qrcode(mode, level)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def avthumb_transcoding(self, frmt, **kwargs):
		fops=QiniuInterface.avthumb_transcoding(frmt, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def avthumb_slice(self, no_domain, **kwargs):
		fops=QiniuInterface.avthumb_slice(no_domain, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def avconcat(self, mode, frmt, *urls):
		fops=QiniuInterface.avconcat(mode, frmt, *urls)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def vframe(self, out_img_frmt, offset, **kwargs):
		fops=QiniuInterface.vframe(out_img_url, offset, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def vsample(self, out_img_frmt, start_time, sample_time, **kwargs):
		fops=QiniuInterface.vsample(
		    out_img_frmt, start_time, sample_time, **kwargs)[1]
		self.__fops.append(fops)
		self.__add_fops_to_resource(fops)
		return self
	def __getattr__(self, attr):
		if attr in ('persistent', 'url', 'get'):
			return getattr(self.__res, attr)
		else:
			raise Exception("No such attribute '%s'" % attr)
	@property
	def fops(self):
		return self.__fops
	def saveas(self, saved_keys, bucket=None, expires=3600):
		bucket=bucket or self.__res.bucket.bucket_name
		base_urls=[]
		saved_ks=[]
		if isinstance(saved_keys, str):
			saved_ks.append(saved_keys)
		else:
			saved_ks.extend(saved_keys)

		assert len(saved_ks) == len(self.__res.key
)
		for key in zip(self.__res.key, saved_ks):
			if self.__res.bucket.acp == 1:
				download_url=self.__res.bucket.private_url(key[0], expires)
				new_url, qs=download_url.split("?")
				new_url=new_url[7:]  # remove http scheme(http://)
				new_url += "?" + "|".join(self.fops)
				interface=QiniuInterface.saveas(key[1], bucket)[1]
				new_url += "|" + interface
				access_token=self.__res.bucket.auth.access_token(new_url)

				base_urls.append("http://" + new_url + '/sign/' + access_token + "&" + qs)
			else:
				download_url=self.__res.bucket.public_url(key[0])
				new_url=download_url[7:]
				new_url += "?" + "|".join(self.fops)
				interface=QiniuInterface.saveas(key[1], bucket)[1]
				new_url += "|" + interface
				access_token=self.__res.bucket.auth.access_token(new_url)
				base_urls.append("http://" + new_url + "/sign/" + access_token)
		self.__res._vpipe["base_url"]=base_urls
		self.__fops=[]
		self.__res._vpipe["fops"]=[]
		return self.__res


class Batch(object):
	def __init__(self, res, cmd=None):
		self.__res=res
		self.__batch_cmd=set()
		if isinstance(cmd, (tuple, list)):
			self.__batch_cmd.update(list(cmd))
	def stat(self, key=None):
		if len(self.__res.key) == 0 and not key:
			raise Exception("resource key can't be empty")
		key=key or self.__res.key[0]
		self.__batch_cmd.add(QiniuInterface.stat(
		    key, self.__res.bucket.bucket_name)[1])
		return self
	def multi_stat(self, keys=None):
		keys=keys or self.__res.key
		for key in keys:
			self.stat(key)
		return self
	def move(self, d_key, d_bucket=None, s_key=None, s_bucket=None):
		s_bucket=s_bucket or self.__res.bucket.bucket_name
		d_bucket=d_bucket or self.__res.bucket.bucket_name
		if len(self.__res.key) == 0 and not s_key:
			raise Exception("resource key can't be empty")
		s_key=s_key or self.__res.key[0]
		self.__batch_cmd.add(QiniuInterface.move(
		    s_key, s_bucket, d_key, d_bucket)[1])
		return self
	def multi_move(self, d_keys, d_bucket=None, s_keys=None, s_bucket=None):
		s_keys=s_keys or self.__res.key()
		if len(s_keys) != len(d_keys):
			raise Exception("'d_keys' must equal to 's_keys'")
		for ds_key in zip(d_keys, s_keys):
			self.move(ds_key[0], d_bucket, ds_key[1], s_bucket)
		return self
	def copy(self, d_key, d_bucket=None, s_key=None, s_bucket=None):
		s_bucket=s_bucket or self.__res.bucket.bucket_name
		d_bucket=d_bucket or self.__res.bucket.bucket_name
		if len(self.__res.key) == 0 and not s_key:
			raise Exception("resource key can't be empty")
		s_key=s_key or self.__res.key[0]
		self.__batch_cmd.add(QiniuInterface.copy(
		    s_key, s_bucket, d_key, d_bucket)[1])
		return self
	def multi_copy(self, d_keys, d_bucket=None, s_keys=None, s_bucket=None):
		s_keys=s_keys or self.__res.key()
		if len(s_keys) != len(d_keys):
			raise Exception("'d_keys' must equal to 's_keys'")
		for ds_key in zip(d_keys, d_keys):
			self.copy(ds_key[0], d_bucket, ds_key[1], s_bucket)
		return self
	def delete(self, key=None):
		if len(self.__res.key) == 0 and not key:
			raise Exception("resource key can't be empty")
		key=key or self.__res.key[0]
		self.__batch_cmd.add(QiniuInterface.delete(
		    key, self.__res.bucket.bucket_name)[1])
		return self
	def multi_delete(self, keys=None):
		keys=keys or self.__res.key
		for key in keys:
			self.delete(key)
		return self
	def list(self, limit=1000, prefix="", delimiter="", marker=""):
		cmd=QiniuInterface.list(self.__res.bucket.bucket_name,
		                        limit, prefix, delimiter, marker)[1]
		self.__batch_cmd.append(cmd)
		return self
	@gen.coroutine
	def execute(self):
		response=yield self.__res.bucket.batch(*self.__batch_cmd)
		return response
	def __getattr__(self, attr):
		if hasattr(self.__res, attr):
			return getattr(self.__res, attr)
		else:
			raise Exception("No such attribute '%s'" % attr)
	@property
	def cmds(self):
		return self.__batch_cmd
##########################################################################
#
#
# Qiniu bucket resource map class
#
#
#
###############################################################################

class Resource(object):
	r"""
		A map class  to qiniu bucket resource
	"""
	def __init__(self, bucket, *key):
		r"""
		Args:
			key:resource key name,
			bucket:bucket object,
		"""
		self.__key=list(key)
		self.__bucket=bucket
		# if len(self._vpipe["base_url"]>0,then len(self._vpipe["base_url"] must
		# equal to len(self.__key)
		self._vpipe={"query_string": [], "url_path": [], "base_url": [], "fops": []}

	@property
	def bucket(self):
		return self.__bucket
	@property
	def key(self):
		return self.__key
	def __reset_vpipe(self):
		self._vpipe["query_string"]=[]
		self._vpipe["url_path"]=[]
		self._vpipe["base_url"]=[]
		self._vpipe["fops"]=[]
	def url(self, expires=3600, return_raw=False):
		path=""
		query_string=""
		urls=[]
		if len(self._vpipe.get("url_path")) > 0:
				path=''.join(self._vpipe.get("url_path"))
		# check last called method whether output a fops
		if len(self._vpipe.get("fops")) > 0:
				query_string += "|".join(self._vpipe.get("fops"))
		# check last called method whether output a query_string
		if len(self._vpipe.get("query_string")) > 0:
				if query_string:
					query_string += '&' + '&'.join(self._vpipe.get("query_string"))
				else:
					query_string += "&".join(self._vpipe.get("query_string"))
		if len(self._vpipe["base_url"]) == 0:
			for key in self.__key:
				url=""
				if self.__bucket.acp == 1:
					url=self.__bucket.private_url(key, expires)
				else:
					url=self.__bucket.public_url(key)
				urls.append(url)
		else:
			urls=self._vpipe["base_url"]

		def concat_url(b_url):
			if b_url.find("?") < 0:
				b_url += path
				if query_string:
					b_url += "?" + query_string

			else:
				if query_string:
					pth, qs=b_url.split('?')
					pth += path + "?" + query_string + "&" + qs
					b_url=pth
			return b_url
		urls=list(map(concat_url, urls))
		self.__reset_vpipe()
		if return_raw:
			return urls
		else:
			if len(urls) == 0:
				return None
			elif len(urls) == 1:
				return urls[0]
			else:
				return urls
	@gen.coroutine
	def get(self, f_name=None):
		return_data=[]
		url=self.url(return_raw=True)
		for key_url in zip(self.__key, url):
			response=yield send_async_request(key_url[1], method="GET", body=None)
			if not response:
				return_data.append(None)
				continue
			response_type=response.headers.get("Content-Type").split("/")[1]
			if response_type != "json":
				if not f_name:
					file_name="./" + key_url[0].rsplit('.', 1)[0] + '.' + response_type
				else:
					file_name=f_name.rsplit('.', 1)[0] + '.' + response_type
				mkdir_recursive(os.path.dirname(file_name))
				with open(file_name, "a+b") as f:
					f.write(response.buffer.read())
				return_data.append(file_name)
			else:
				return_data.append(json_decode(bytes_decode(response.body)))
		if len(return_data) == 0:
			return None
		if len(return_data) == 1:
			return return_data[0]
		else:
			return return_data
	@gen.coroutine
	def put(self, filename, host="upload.qiniu.com", accept="json"):
		responses=[]
		for key in self.__key:
			response=yield self.__bucket.put(key, filename, host, accept)
			responses.append(response)
		if len(responses) == 1:
			return responses[0]
		else:
			return responses
	@gen.coroutine
	def stat(self):
		response=yield self.__bucket.stat(self.__key[0], self.__bucket.bucket_name)
		if response:
			return json_decode(response)
	@gen.coroutine
	def multi_stat(self):
		batch=self.batch()
		batch.multi_stat()
		response=yield batch.execute()
		if response:
			return json_decode(response)
	@gen.coroutine
	def delete(self):
		response=yield self.__bucket.delete(self.__key, self.__bucket.bucket_name)
		if response:
			return json_decode(response)
	@gen.coroutine
	def multi_delete(self):
		batch=self.batch()
		batch.multi_delete()
		response=yield batch.execute()
		if response:
			return json_decode(resposne)
	@gen.coroutine
	def list(self, limit=1000, prefix="", delimiter="", marker=""):
		response=yield self.__bucket.list(self.__bucket.bucket_name, limit, prefix, delimiter, marker)
		if response:
			return json_decode(response)
	@gen.coroutine
	def moveto(self, dest_key, dest_bucket=None):
		dest_bucket=dest_bucket or self.__res.bucket.bucket_name
		response=yield self.__bucket.move(self.__key, self.__bucket.bucket_name, dest_key, dest_bucket or self.__bucket.bucket_name)
		if response:
			return json_decode(response)
	@gen.coroutine
	def multi_moveto(self, dest_keys, dest_bucket=None):
		batch=self.batch()
		batch.multi_move(dest_keys)
		response=yield batch.execute()
		if response:
			return json_decode(response)
	@gen.coroutine
	def copyto(self, dest_key, dest_bucket=None):
		dest_bucket=dest_bucket or self.__res.bucket.bucket_name
		response=yield self.__bucket.copy(self.__key, self.__bucket.bucket_name, dest_key, dest_bucket)
		if response:
			return json_decode(response)
	@gen.coroutine
	def multi_copyto(self, dest_keys, dest_bucket):
		batch=self.batch()
		batch.multi_copy(dest_keys)
		response=yield batch.execute()
		if response:
			return json_decode(response)
	def batch(self, cmd=None):
		return Batch(self, cmd)
	@gen.coroutine
	def fetch_store(self, fetch_url):
		response=yield self.__bucket.fetch_store(fetch_url, self.__key, self.__bucket.bucket_name)
		if response:
			return json_decode(response)
	@gen.coroutine
	def prefetch(self):
		response=yield self.__bucket.prefetch(self.__key, self.__bucket.bucket_name)
		if response:
			return json_decode(response)
	@gen.coroutine
	def persistent(self, notify_url, pipeline=None, force=1):
		persistent=self.__bucket.persistent(
		    self.__key, notify_url, fops, force, pipeline)
		persistent.add_multi_fops(self._vpipe["fops"])
		response=yield persistent.execute()
		if response:
			return json_deocde(response)
	@gen.coroutine
	def prefop(self, persistent_id):
		response=yield self.__bucket.prefop(persistent_id)
		if response:
			return json_decode(response)
	def fops(self, ops=None):
		return Fops(ops, self)
	def imageinfo(self):
		self._vpipe["query_string"].append(QiniuInterface.imageinfo()[1])
		return self
	def imageexif(self):
		self._vpipe["query_string"].append(QiniuInterface.imageexif()[1])
		return self
	def imageave(self):
		self._vpipe["query_string"].append(QiniuInterface.imageave()[1])
		return self
	def avinfo(self):
		self._vpipe["query_string"].append(QiniuInterface.avinfo()[1])
		return self
