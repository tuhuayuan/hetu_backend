import base64
import hashlib
import random
import string
from datetime import datetime, timezone

import jwt
from captcha.image import ImageCaptcha
from casbin_adapter.enforcer import enforcer
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja.security import HttpBearer

from apps.auth.adapter import RoleManager
from apps.auth.models import Department, DictData, DictType, Role, User
from apps.auth.schemas import (
    CaptchaOut,
    DepartmentIn,
    DepartmentOut,
    DepartmentUpdateIn,
    DictDataIn,
    DictDataOut,
    DictTypeIn,
    DictTypeOut,
    LoginIn,
    LoginOut,
    RoleIn,
    RoleOut,
    RoleUpdateIn,
    UserCreateIn,
    UserOut,
    UserPasswordIn,
    UserUpdateIn,
)
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

enforcer.set_role_manager(RoleManager())
enforcer.load_policy()

router = Router()


@router.get("/roles", response=list[RoleOut])
@api_schema
def list_roles(request):
    """角色列表接口"""

    return Role.objects.all()


@router.get("/roles/{role_id}", response=RoleOut)
@api_schema
def get_role(request, role_id: int):
    """角色信息接口"""

    try:
        d = get_object_or_404(Role, id=role_id)
    except Exception as e:
        raise HttpError(404, str(e))

    return d


@router.post("/roles", response=RoleOut)
@api_schema
def create_roles(request, payload: RoleIn):
    """创建角色接口"""

    r = Role(create_time=datetime.now(timezone.utc), **payload.dict())

    try:
        r.save()
    except IntegrityError:
        raise HttpError(403, "角色代码已存在")
    return r


@router.post("/roles/{role_id}", response=RoleOut)
@api_schema
def update_roles(request, role_id: int, payload: RoleUpdateIn):
    """修改角色接口"""

    try:
        r = get_object_or_404(Role, id=role_id)
    except Exception as e:
        raise HttpError(404, str(e))

    r.name = payload.name
    r.status = payload.status
    r.sort = payload.status

    r.save()
    return r


@router.get("/depts", response=list[DepartmentOut])
@api_schema
def list_department(request):
    """部门列表接口"""

    return Department.objects.all()


@router.get("/depts/{dept_id}", response=DepartmentOut)
@api_schema
def get_department(request, dept_id: int):
    """获取单个部门"""

    try:
        d = get_object_or_404(Department, id=dept_id)
    except Exception as e:
        raise HttpError(404, str(e))

    return d


@router.post("/depts", response=DepartmentOut)
@api_schema
def create_department(request, payload: DepartmentIn):
    """创建部门接口"""

    d = Department(create_time=datetime.now(timezone.utc), **payload.dict())
    d.save()
    return d


@router.post("/depts/{dept_id}", response=DepartmentOut)
@api_schema
def update_department(request, dept_id: int, payload: DepartmentUpdateIn):
    """更新部门信息接口"""

    try:
        d = get_object_or_404(Department, id=dept_id)
    except Exception as e:
        raise HttpError(404, str(e))

    d.description = payload.description
    d.status = payload.status

    d.save()
    return d


@router.get("/users", response=list[UserOut])
@api_paginate
def list_user(request):
    """用户列表接口"""

    output_list: list[UserOut] = []
    users = User.objects.all()

    for u in users:
        out = UserOut.from_orm(u)
        out.roles_id = [r.id for r in u.roles.all()]
        out.roles_name = [r.name for r in u.roles.all()]
        out.dept_name = u.dept.name
        output_list.append(out)

    return output_list


def _get_password(password: str) -> str:
    """计算密码hash"""

    password = settings.SECRET_KEY + password

    return hashlib.sha1(password.encode()).hexdigest()


def _get_captcha(captcha_text: str) -> str:
    """计算验证码hash"""

    captcha_text = settings.SECRET_KEY + captcha_text.lower()

    # 计算验证码字符串的SHA1哈希值
    return hashlib.sha1(captcha_text.encode()).hexdigest()


def _get_token(user: User) -> str:
    """获取JWT令牌"""

    token = {
        "username": user.username,
    }

    return jwt.encode(token, settings.SECRET_KEY, algorithm="HS256")


@router.post("/users", response=UserOut)
@api_schema
def create_user(request, payload: UserCreateIn):
    """用户创建接口"""
    try:
        d = get_object_or_404(Department, id=payload.dept_id)
        roles = Role.objects.filter(id__in=payload.roles_id)

        if not roles:
            raise Http404("找不到所属角色")

    except Http404 as e:
        raise HttpError(400, f"部门或角色错误 {str(e)}")

    u = User(
        dept=d,
        create_time=datetime.now(timezone.utc),
        **payload.dict(exclude={"dept_id": True, "roles_id": True}),
    )
    try:
        u.password = _get_password(payload.password)

        u.save()
        u.roles.set(roles)
    except IntegrityError:
        raise HttpError(400, "用户添加失败, 用户已存在")
    except Exception as e:
        raise HttpError(500, f"用户添加失败： {str(e)}")

    out = UserOut.from_orm(u)
    out.roles_id = [r.id for r in u.roles.all()]
    out.roles_name = [r.name for r in u.roles.all()]
    out.dept_name = u.dept.name

    return out


@router.get("/users/{user_id}", response=UserOut)
@api_schema
def get_user(request, user_id: int):
    """用户信息接口"""

    try:
        u = get_object_or_404(User, id=user_id)
    except Http404:
        raise HttpError(404, "用户不存在")

    out = UserOut.from_orm(u)
    out.roles_id = [r.id for r in u.roles.all()]
    out.roles_name = [r.name for r in u.roles.all()]
    out.dept_name = u.dept.name

    return out


@router.post("/users/{user_id}", response=UserOut)
@api_schema
def update_user(request, user_id: int, payload: UserUpdateIn):
    """用户修改接口"""

    try:
        u = get_object_or_404(User, id=user_id)
    except Http404:
        raise HttpError(404, "用户不存在")

    try:
        d = get_object_or_404(Department, id=payload.dept_id)
        roles = Role.objects.filter(id__in=payload.roles_id)

        if not roles:
            raise Http404("找不到所属角色")

    except Http404 as e:
        raise HttpError(400, f"部门或角色错误 {str(e)}")

    u.nickname = payload.nickname
    u.mobile = payload.mobile
    u.gender_label = payload.gender_label
    u.avatar = payload.avatar
    u.email = payload.email
    u.status = payload.status
    u.dept = d
    u.roles.set(roles)
    u.save()

    out = UserOut.from_orm(u)
    out.roles_id = [r.id for r in u.roles.all()]
    out.roles_name = [r.name for r in u.roles.all()]
    out.dept_name = u.dept.name
    return out


@router.post("/users/{user_id}/password", response=str)
@api_schema
def change_password(request, user_id: int, payload: UserPasswordIn):
    """修改密码接口"""

    try:
        u = get_object_or_404(User, id=user_id)
    except Http404:
        raise HttpError(404, "用户不存在")

    u.password = _get_password(payload.password)
    u.save()
    return "OK"


@router.get("/captcha", response=CaptchaOut)
@api_schema
def get_captcha(request):
    # 生成随机的4个字符验证码
    captcha_text = "".join(random.choices(string.ascii_letters + string.digits, k=4))

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
    """登陆接口"""

    # 先检测验证码
    if _get_captcha(payload.verify_code) != payload.verify_code_key:
        raise HttpError(401, "验证码错误")

    u = User.objects.filter(
        username=payload.username, password=_get_password(payload.password), status=1
    ).first()
    if not u:
        raise HttpError(401, "用户名或密码错误")

    out = LoginOut(
        access_token=_get_token(u),
        token_type="Bearer",
    )
    return out


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

            # 只需要满足任意一项配置的权限
            for p in self._perms:
                obj = p[0].format(username=login_token["username"])
                act = p[1].format(methoed=request.method)

                # 验证调用权限
                if enforcer.enforce(login_token["username"], obj, act):
                    return login_token

            # 所有权限验证都失败
            raise PermissionDenied("没有权限")

        # 这两个错误可以区分处理
        except jwt.InvalidSignatureError:
            return None
        except PermissionDenied:
            return None


@router.get(
    "/bearer", auth=AuthBearer([("sys:auth:user:{username}:info", "rw")]), response=dict
)
@api_schema
def bearer(request):
    return request.auth


@router.post(
    "/dict/types",
    response=DictTypeOut,
    auth=AuthBearer([("api:auth:dict:types", "rw")]),
)
@api_schema
def create_dicttype(request, payload: DictTypeIn):
    """创建字典类型接口"""
    try:
        dt = DictType(**payload.dict())
        dt.save()

        return dt
    except IntegrityError:
        raise HttpError(400, "创建失败: code重复")


@router.get(
    "/dict/types",
    response=list[DictTypeOut],
    auth=AuthBearer([("api:auth:dict:types", "r")]),
)
@api_paginate
def list_dicttype(request):
    """字典类型列表接口"""
    return DictType.objects.all()


@router.get(
    "/dict/types/{dicttype_id}",
    response=DictTypeOut,
    auth=AuthBearer([("api:auth:dict:types", "r")]),
)
@api_schema
def get_dicttype(request, dicttype_id: int):
    """字典类型接口"""
    try:
        dt = get_object_or_404(DictType, id=dicttype_id)
        return dt
    except:
        raise HttpError(404, "字典类型不存在")


@router.post(
    "/dict/types/{dicttype_id}",
    response=DictTypeOut,
    auth=AuthBearer([("api:auth:dict:types", "rw")]),
)
@api_schema
def update_dicttype(request, dicttype_id: int, payload: DictTypeIn):
    """字典类型更新信息接口"""
    try:
        dt = get_object_or_404(DictType, id=dicttype_id)
        dt.name = payload.name
        dt.code = payload.code
        dt.status = payload.status
        dt.remark = payload.remark

        dt.save()
        return dt
    except IntegrityError:
        raise HttpError(400, "字典Code重复")
    except:
        raise HttpError(404, "字典类型不存在")


@router.delete(
    "/dict/types/{dicttype_id}",
    response=str,
    auth=AuthBearer([("api:auth:dict:types", "rw")]),
)
@api_schema
def delete_dicttype(request, dicttype_id: int):
    """字典类型删除接口"""
    try:
        dt = get_object_or_404(DictType, id=dicttype_id)
        dt.delete()
        return "OK"
    except:
        raise HttpError(404, "字典类型不存在")


@router.post(
    "/dict/data/{dicttype_id}",
    response=DictDataOut,
    auth=AuthBearer([("api:auth:dict:data", "rw")]),
)
@api_schema
def create_dictdata(request, dicttype_id: int, payload: DictDataIn):
    """字典数据创建"""
    try:
        dd = DictData(**payload.dict())
        dd.dict_type_id = dicttype_id
        dd.save()

        return dd
    except IntegrityError as err:
        raise HttpError(400, f"创建失败: {str(err)}")


@router.get(
    "/dict/data/{dicttype_id}",
    response=list[DictDataOut],
    auth=AuthBearer([("api:auth:dict:data", "r")]),
)
@api_paginate
def list_dictdata(request, dicttype_id: int):
    """字典数据列表"""
    return DictData.objects.filter(dict_type_id=dicttype_id).all()


@router.get(
    "/dict/data/{dicttype_id}/{dictdata_id}",
    response=DictDataOut,
    auth=AuthBearer([("api:auth:dict:data", "r")]),
)
@api_schema
def get_dictdata(request, dicttype_id: int, dictdata_id: int):
    """字典数据信息"""
    dd = DictData.objects.filter(id=dictdata_id, dict_type_id=dicttype_id).first()
    if not dd:
        raise HttpError(404, "字典数据不存在")
    return dd


@router.post(
    "/dict/data/{dicttype_id}/{dictdata_id}",
    response=DictDataOut,
    auth=AuthBearer([("api:auth:dict:data", "rw")]),
)
@api_schema
def update_dictdata(request, dicttype_id: int, dictdata_id: int, payload: DictDataIn):
    """字典数据信息更新"""
    dd = DictData.objects.filter(id=dictdata_id, dict_type_id=dicttype_id).first()
    if not dd:
        raise HttpError(404, "字典数据不存在")
    dd.label = payload.label
    dd.value = payload.value
    dd.status = payload.status
    dd.sort = payload.sort
    dd.remark = payload.remark

    dd.save()
    return dd


@router.delete( 
    "/dict/data/{dicttype_id}/{dictdata_id}",
    response=str,
    auth=AuthBearer([("api:auth:dict:data", "rw")]),
)
@api_schema
def delete_dictdata(request, dicttype_id: int, dictdata_id: int):
    dd = DictData.objects.filter(id=dictdata_id, dict_type_id=dicttype_id).first()
    if not dd:
        raise HttpError(404, "字典数据不存在")
    dd.delete()
    return 'OK'
