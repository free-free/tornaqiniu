#-*- coding:utf-8 -*-


from .utils import *
import functools


def encode_entry(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if len(args) == 2:
            encoded_entry = bytes_decode(
                urlsafe_base64_encode(args[1] + ':' + args[0]))
            return method(self, encoded_entry)
        elif len(args) == 4:
            src_entry = bytes_decode(
                urlsafe_base64_encode(args[1] + ":" + args[0]))
            dest_entry = bytes_decode(urlsafe_base64_encode(
                str(args[3]) + ":" + str(args[2])))
            return method(self, src_entry, dest_entry)
    return wrapper


class QiniuInterface(object):

    @classmethod
    @encode_entry
    def stat(cls, entry):
        interface = "/stat/" + entry
        return ('rs.qiniu.com', interface)

    @classmethod
    @encode_entry
    def move(cls, src_entry, dest_entry):
        interface = "/move/" + src_entry.strip() + "/" + dest_entry.strip()
        return ('rs.qiniu.com', interface)

    @classmethod
    @encode_entry
    def copy(cls, src_entry, dest_entry):
        interface = "/copy/" + src_entry.strip() + '/' + dest_entry.strip()
        return ('rs.qiniu.com', interface)

    @classmethod
    @encode_entry
    def delete(cls, entry):
        interface = "/delete/" + entry
        return ('rs.qiniu.com', interface)

    @classmethod
    def list(cls, bucket, limit, prefix, delimiter, marker):
        query_string = urlencode({
            'bucket': bucket,
            'limit': limit,
            'marker': marker,
            'prefix': prefix,
            'delimiter': delimiter
        })
        interface = "/list?" + query_string
        return ('rsf.qbox.me', interface)

    @classmethod
    def fetch_store(cls, fetch_url, key, bucket):
        encoded_entry = bytes_decode(urlsafe_base64_encode(bucket + ':' + key))
        encoded_url = bytes_decode(urlsafe_base64_encode(fetch_url))
        interface = "/fetch/" + encoded_url + '/to' + encoded_entry
        return ('iovip.qbox.me', interface)

    @classmethod
    def batch(cls, *opers):
        pass

    @classmethod
    @encode_entry
    def prefetch(cls, entry):
        interface = '/prefetch/' + entry
        return ("iovip.qboix.me", interface)

    @classmethod
    def image_watermark(cls, water_img_url, **kwargs):
        interface = "watermark/1"
        interface += '/image/' + \
            str(bytes_decode(urlsafe_base64_encode(water_img_url)))
        if len(kwargs) > 0:
            valid_fields = set(['gravity', 'dx', 'dissolve', 'dy', 'ws'])
            for field, value in kwargs.items():
                if field not in valid_fields:
                    raise Exception("Not support field '%s'" % field)
                interface += '/' + str(field) + '/' + str(value)
        return ("", interface)

    @classmethod
    def text_watermark(cls, text, **kwargs):
        interface = "watermark/2"
        interface += '/text/' + str(bytes_decode(urlsafe_base64_encode(text)))
        if len(kwargs) > 0:
            valid_fields = set(
                ['font', 'font_size', 'fontsize', 'fill', 'dissolve', 'gravity', 'dx', 'dy'])
            urlsafe_encode_fields = set(['font', 'fill'])
            for field, value in kwargs.items():
                if field not in valid_fields:
                    raise Exception("Not support field '%s'" % field)
                if field in urlsafe_encode_fields:
                    interface += '/' + \
                        str(field) + '/' + \
                        str(bytes_decode(urlsafe_base64_encode(value)))
                else:
                    interface += '/' + str(field) + '/' + str(value)
        return ("", interface)

    @classmethod
    def image_view2(cls, mode, width=None, height=None, **kwargs):
        assert width or height, "both width and height can't be none"
        interface = "imageViesw2/" + str(mode)
        if width:
            interface += '/w/' + str(width)
        if height:
            interface += '/h/' + str(height)
        if len(kwargs) > 0:
            valid_fields = set(
                ['format', 'interlace', 'quality', 'ignor-error'])
            for field, value in kwargs.items():
                if field not in valid_fields:
                    raise Exception("Not support field '%s'" % field)
                interface += '/' + str(field) + '/' + str(value)
        return ("", interface)

    @classmethod
    def qrcode(cls, mode, level):
        interface = 'qrcode/' + str(mode) + '/level/' + str(level)
        return ("", interface)

    @staticmethod
    def _options_dict_to_str(options):
        options_list = list(options.items())
        options_list = list(
            map(lambda item: "/" + str(item[0]) + "/" + str(item[1]), options_list))
        options_str = reduce(lambda op1, op2: op1 + op2, options_list)
        return options_str

    @classmethod
    def avthumb_transcoding(cls, frmt, **kwargs):
        interface = "avthumb/%s" % tr(frmt)
        if len(kwargs) > 0:
            interface += _options_dict_to_str(kwargs)
        return ("", interface)

    @classmethod
    def avthumb_slice(cls, no_domain, **kwargs):
        if int(no_domain) > 0:
            no_domain = 1
        else:
            no_domain = 0
        interface = 'authumb/m3u8/noDomain/%s' % str(no_domain)
        if len(kwargs) > 0:
            interface += _options_dict_to_str(kwargs)
        return ("", interface)

    @classmethod
    def avconcat(cls, mode, frmt, *urls):
        interface = 'avconcat/' + str(mode) + '/format/' + str(frmt)
        for url in urls:
            interface += '/' + bytes_decode(urlsafe_base64_encode(url))
        return ("", interface)

    @classmethod
    def vframe(cls, out_img_frmt, offset, **kwargs):
        interface = "vframe/" + str(out_img_frmt) + '/offset/' + str(offset)
        if len(kwargs) > 0:
            for field, value in kwargs.items():
                interface += '/' + field + '/' + str(value)
        return ("", interface)

    @classmethod
    def vsample(cls, out_img_frmt, start_second, sample_time, **kargs):
        interface = "vsample/" + str(out_img_frmt) + '/ss/' + str(start_second)
        interface += '/t/' + str(sample_time)
        if len(kwargs) > 0:
            urlsafe_encode_fields = set(['pattern'])
            for field, value in kwargs.items():
                if field not in urlsafe_encode_fields:
                    interface += '/' + str(field) + '/' + str(value)
                else:
                    interface + '/' + \
                        str(field) + '/' + \
                        bytes_decode(urlsafe_base64_encode(value))
        return ("", interface)

    @classmethod
    def prefop(cls, persistent_id):
        interface = "/status/get/prefop?id=%s" % str(persistent_id)
        return ("", interface)

    @classmethod
    def imageinfo(self):
        return ("", "imageInfo")

    @classmethod
    def imageexif(self):
        return ("", "exif")

    @classmethod
    def imageave(self):
        return ("", "imageAve")

    @classmethod
    def avinfo(self):
        return ("", "avinfo")

    @classmethod
    def saveas(self, key, bucket):
        encoded_entry = bytes_decode(urlsafe_base64_encode(bucket + ':' + key))
        interface = "saveas/" + encoded_entry
        return ("", interface)
