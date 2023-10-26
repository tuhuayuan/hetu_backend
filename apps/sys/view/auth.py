import base64
from datetime import datetime, timedelta, timezone
import hashlib
import random
import string

from captcha.image import ImageCaptcha
from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from apps.sys.models import User
from apps.sys.schemas import CaptchaOut, LoginIn, LoginOut
from apps.sys.utils import get_captcha, get_password, get_token
from utils.schema.base import api_schema

router = Router()


@router.get("/captcha", response=CaptchaOut)
@api_schema
def captcha(request):
    # 生成随机的4个字符验证码
    captcha_text = "".join(random.choices(string.digits, k=4))

    # 使用captcha库生成验证码图片
    image = ImageCaptcha()
    captcha_image = image.generate(captcha_text)

    # 将验证码图片编码为base64
    captcha_image_base64 = base64.b64encode(captcha_image.getvalue()).decode()

    captcha_text = settings.SECRET_KEY + captcha_text.lower()

    # 计算验证码字符串的SHA1哈希值
    sha1_hash = hashlib.sha1(captcha_text.encode()).hexdigest()

    return {
        "verify_code_base64": "data:image/png;base64," + captcha_image_base64,
        "verify_code_key": sha1_hash,
    }


@router.post("/login", response=LoginOut)
@api_schema
def login(request, payload: LoginIn):

    # 先检测验证码
    if get_captcha(payload.verify_code) != payload.verify_code_key:
        if not settings.DEBUG:
            raise HttpError(401, "验证码错误")

    u = User.objects.filter(
        username=payload.username, password=get_password(payload.password), status=1
    ).first()
    if not u:
        raise HttpError(401, "用户名或密码错误")

    expires = datetime.now(timezone.utc) + timedelta(days=1)
    out = LoginOut(
        access_token=get_token(u, expires),
        token_type="Bearer",
        expires=expires,
    )
    return out


@router.delete("/logout", response=str)
@api_schema
def logout(request):
    return 'ok'