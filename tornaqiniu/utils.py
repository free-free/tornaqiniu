#-*- coding:utf-8 -*-

import base64
import hmac
import json
import urllib
from tornado import gen
from tornado import httpclient
from tornado.httpclient import AsyncHTTPClient
import os
import time
import random
import hashlib


def json_encode(need_encode):
    return json.dumps(need_encode)


def json_decode(need_decode):
    return json.loads(need_decode)


def bytes_encode(need_encode, encoding="utf-8"):
    if not isinstance(need_encode, bytes):
        return str(need_encode).encode(encoding)
    return need_encode


def bytes_decode(need_decode, encoding="utf-8"):
    if isinstance(need_decode, bytes):
        return need_decode.decode(encoding)
    return str(need_decode)


def urlsafe_base64_encode(need_encode):
    if isinstance(need_encode, str):
        bytes_encoded = bytes_encode(need_encode)
        return base64.urlsafe_b64encode(bytes_encoded)
    elif isinstance(need_encode, bytes):
        return base64.urlsafe_b64encode(need_encode)
    else:
        raise EncodingError("'need_encode' must be str or bytes type")


def hmac_sha1(key, data):
    bytes_key = bytes_encode(key)
    bytes_data = bytes_encode(data)
    return hmac.new(bytes_key, bytes_data, 'sha1').digest()


def urlencode(need_encode):
    return urllib.parse.urlencode(need_encode)


@gen.coroutine
def send_async_request(url, headers=None, method="GET", body=None):
    headers = headers or {}
    if body or method.upper() == "POST":
        if 'Content-Type' not in headers:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = httpclient.HTTPRequest(
        url, method=method, body=body, headers=headers, allow_nonstandard_methods=True)
    http_request = AsyncHTTPClient()
    response = ""
    try:
        response = yield http_request.fetch(req)
    except httpclient.HTTPError as e:
        print("Error:" + str(e))
    except Exception as e:
        print("Error:" + str(e))
    else:
        return response
    finally:
        http_request.close()


def send_sync_request(url, headers=None, method="GET", body=None):
    headers = headers or {}
    if body or method.upper() == "POST":
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = httpclient.HTTPRequest(
        url, method=method, body=body, headers=headers, allow_nonstandard_methods=True)
    http_client = httpclient.HTTPClient()
    response = ""
    try:
        response = http_client.fetch(req)
        return response
    except httpclient.HTTPError as e:
        print("Error:" + str(e))
        raise httpclient.HTTPError()
    except Exception as e:
        print("Error:" + str(e))
        raise Exception
    finally:
        http_client.close()


def mkdir_recursive(dirname, level=1):
    if level == 1:
        dirname = os.path.abspath(dirname)
    if not os.path.exists(os.path.dirname(dirname)):
        mkdir_recursive(os.path.dirname(dirname), level + 1)
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def multipart_formdata(fields, files):
    md5 = hashlib.md5()
    md5.update(str(random.random()).encode())
    boundary = '-----' + md5.hexdigest()
    CRLF = b'\r\n'
    data = []
    for key, value in fields.items():
        data.append(('--' + boundary).encode())
        data.append(('Content-Disposition: form-data; name="%s"' %
                     key).encode())
        data.append(b'')
        data.append(value.encode())
    for key, filename in files.items():
        data.append(('--' + boundary).encode())
        data.append(('Content-Disposition:form-data; name="%s"; filename="%s"' %
                     (key, filename)).encode())
        data.append(('Content-Type: application/octet-stream').encode())
        data.append(("Content-Transfer-Encoding: binary").encode())
        data.append(b'')
    with open(filename, "r+b") as f:
        data.append(f.read())
    data.append(('--' + boundary + '--').encode())
    data.append(b'')
    data = CRLF.join(data)
    content_type = "multipart/form-data; boundary=%s" % boundary
    return content_type, data
