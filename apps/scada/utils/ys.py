import json
from django.conf import settings
from django.core.cache import cache
import requests
from functools import wraps


ACCESS_TOKEN = ''


def with_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # 假设resp_json是一个字典
            if str(e) == "10002":
                global ACCESS_TOKEN
                ACCESS_TOKEN = get_accecc_token()
                return func(*args, **kwargs)
            else:
                raise Exception(f"ys error_code: {e}")

    return wrapper


def with_cache(cache_time=60*60):
    def decorator(func):
        @wraps(func)
        def wrapper(device_serial, channel_no, *args, **kwargs):
            cache_key = f"{device_serial}_{channel_no}"  # 使用 device_serial 和 channel_no 作为缓存的键
            cached_data = cache.get(cache_key)

            if cached_data:
                return json.loads(cached_data)
            else:
                result = func(device_serial, channel_no, *args, **kwargs)
                cache.set(cache_key, json.dumps(result), timeout=cache_time)  # 设置缓存时间
                return result
        return wrapper
    return decorator


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


@with_token
@with_cache(60)
def get_capture_url(device_serial: str, channel_no: int = 1, quality: int = 3) -> str:
    """获取通道截图"""

    url = "https://open.ys7.com/api/lapp/device/capture"

    payload = f"accessToken={ACCESS_TOKEN}&deviceSerial={device_serial}&channelNo={channel_no}&quality={quality}"
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


@with_token
@with_cache(60*60)
def get_video_url(device_serial: str, channel_no: int = 1) -> str:
    """获取视频播放地址"""

    url = "https://open.ys7.com/api/lapp/v2/live/address/get"

    payload = f"accessToken={ACCESS_TOKEN}&deviceSerial={device_serial}&channelNo={channel_no}&expireTime=604800&protocol=4"
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
