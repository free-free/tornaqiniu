#-*- coding:utf-8 -*-

import base64
import hmac
import json
from .errors import *


def json_encode(need_encode):
	return json.dumps(need_encode)

def json_decode(need_decode):
	return json.loads(need_decode)

def bytes_encode(need_encode,encoding="utf-8"):
	if not isinstance(need_encode,bytes):
		return str(need_encode).encode(encoding)
	return need_encode

def bytes_decode(need_decode,encoding="utf-8"):
	if isinstance(need_decode,bytes):
		return need_decode.decode(encoding)
	return str(need_decode)

def urlsafe_base64_encode(need_encode):
	if isinstance(need_encode,str):
		bytes_encoded=bytes_encode(need_encode)
		return  base64.urlsafe_b64encode(bytes_encoded)
	elif isinstance(need_encode,bytes):
		return base64.urlsafe_b64encode(need_encode)
	else:
		raise EncodingError("'need_encode' must be str or bytes type")

def hmac_sha1(key,data):
	bytes_key=bytes_encode(key)
	bytes_data=bytes_encode(data)
	return hmac.new(bytes_key,bytes_data,'sha1').digest()

	
