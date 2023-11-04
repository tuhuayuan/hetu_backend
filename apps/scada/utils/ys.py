import json
from django.conf import settings
from django.core.cache import cache
import requests
from functools import wraps


def with_cache(cache_time=60*60, device_serial='ys', channel_no=0, action=''):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key0 = kwargs.get('device_serial', device_serial)
            key1 = kwargs.get('channel_no', channel_no)
            key2 = kwargs.get('action', action)

            cache_key = f"{key0}_{key1}_{key2}"  # 使用 device_serial 和 channel_no 作为缓存的键
            cached_data = cache.get(cache_key)

            if cached_data:
                return json.loads(cached_data)
            else:
                result = func(*args, **kwargs)
                cache.set(cache_key, json.dumps(result), timeout=cache_time)  # 设置缓存时间
                return result
        return wrapper
    return decorator


@with_cache(cache_time=60*60*24)
def get_accecc_token() -> str:
    """获取访问TOKEN"""

    appKey = settings.YS_APPKEY
    appSecret = settings.YS_APPSECRET
    url = (
        f"https://open.ys7.com/api/lapp/token/get?appKey={appKey}&appSecret={appSecret}"
    )
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    resp = requests.request("POST", url, headers=headers, data={}, timeout=5)
    resp.raise_for_status()

    resp_json = resp.json()
    if resp_json['code'] == "200":
        return resp_json['data']['accessToken']
    else:
        raise Exception(resp_json["code"])


@with_cache(60, action='capture')
def get_capture_url(device_serial: str = '', channel_no: int = 1, quality: int = 3) -> str:
    """获取通道截图"""

    url = "https://open.ys7.com/api/lapp/device/capture"
    token = get_accecc_token()

    payload = f"accessToken={token}&deviceSerial={device_serial}&channelNo={channel_no}&quality={quality}"
    headers = {
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = requests.request("POST", url, headers=headers, data=payload, timeout=5)
    resp.raise_for_status()

    resp_json = resp.json()
    if resp_json["code"] == "200":
        return resp_json["data"]["picUrl"]
    else:
        raise Exception(resp_json["code"])


@with_cache(60*60, action='video')
def get_video_url(device_serial: str = '', channel_no: int = 1, protocol=1) -> str:
    """获取视频播放地址"""

    url = "https://open.ys7.com/api/lapp/v2/live/address/get"
    token = get_accecc_token()

    payload = f"accessToken={token}&deviceSerial={device_serial}&channelNo={channel_no}&expireTime=604800&protocol={protocol}"
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    resp = requests.request("POST", url, headers=headers, data=payload)
    resp.raise_for_status()

    resp_json = resp.json()
    if resp_json['code'] == "200":
        return resp_json['data']['url']
    else:
        raise Exception(resp_json['code'])
