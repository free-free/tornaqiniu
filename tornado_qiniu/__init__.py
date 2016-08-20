#-*- coding:utf-8 -*-
__email__ = "19941222hb@gmail.com"
__author__ = "HuangBiao"
__version__ = "1.2"

PUT_POLICY = {
    "scope": {"type": str, "value": ""},
    "deadline": {"type": int, "value": ""},
    "insertOnly": {"type": str, "value": ""},
    "endUser": {"type": str, "value": ""},
    "returnUrl": {"type": str, "value": ""},
    "returnBody": {"type": str, "value": ""},
    "callbackUrl": {"type": str, "value": ""},
    "callbackHost": {"type": str, "value": ""},
    "callbackBody": {"type": str, "value": ""},
    "callbackBodyType": {"type": str, "value": ""},
    "callBackFetchKey": {"type": int, "value": 0},
    "persistentOps": {"type": str, "value": ""},
    "persistentNotifyUrl": {"type": str, "value": ""},
    "persistentPipeline": {"type": str, "value": ""},
    "saveKey": {"type": str, "value": ""},
    "fsizeMin": {"type": int, "value": 0},
    "fsizeLimit": {"type": int, "value": 0},
    "detectMime": {"type": int, "value": 1},
    "mimeLimit": {"type": str, "value": ""},
    "deleteAfterDays": {"type": int, "value": -1}
}

from .common import Policy
from .client import QiniuClient
__all__ = ("QiniuClient",)
