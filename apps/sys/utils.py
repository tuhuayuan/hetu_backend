import hashlib
from datetime import datetime

import jwt
from casbin_adapter.enforcer import enforcer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from ninja.security import HttpBearer

from apps.sys.models import User


def get_password(password: str) -> str:
    """计算密码hash"""

    password = settings.SECRET_KEY + password
    return hashlib.sha1(password.encode()).hexdigest()


def get_captcha(captcha_text: str) -> str:
    """计算验证码hash"""

    captcha_text = settings.SECRET_KEY + captcha_text.lower()
    return hashlib.sha1(captcha_text.encode()).hexdigest()


def get_token(user: User, expires: datetime) -> str:
    """获取JWT令牌"""

    token = {"id": user.id, "username": user.username, "expires": expires.isoformat()}
    return jwt.encode(token, settings.SECRET_KEY, algorithm="HS256")


class AuthBearer(HttpBearer):
    """JWT认证"""

    def __init__(self, perms: list[tuple[str, str]] = []):
        self._perms = perms
        super().__init__()

    def authenticate(self, request, token):

        try:
            login_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            # 无需权限控制
            if not self._perms:
                return login_token

            enforcer.load_policy()

            # 只需要满足任意一项配置的权限
            for p in self._perms:
                obj = p[0].format(username=login_token["username"])
                act = p[1].format(methoed=request.method)

                # 验证调用权限
                if enforcer.enforce(login_token["username"], obj, act):
                    return login_token

            # 所有权限验证都失败
            raise PermissionDenied("没有权限")
        except:
            return None
