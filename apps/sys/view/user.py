from datetime import datetime, timezone

from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from casbin_adapter.enforcer import enforcer

from apps.sys.models import Department, User
from apps.sys.schemas import (
    UserBase,
    UserCreateIn,
    UserCreateOut,
    UserLoginInfoOut,
    UserListOut,
    UserPasswordIn,
    UserUpdateIn,
)
from apps.sys.utils import AuthBearer, get_password
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post(
    "",
    response=UserCreateOut,
    auth=AuthBearer([("sys:user:add", "x")]),
)
@api_schema
def create_user(request, payload: UserCreateIn):
    """创建用户"""

    payload.password = get_password(payload.password)
    u = User(
        create_time=datetime.now(timezone.utc),
        **payload.dict(exclude={"role_ids": True}),
    )
    u.save()

    # 保存角色
    u.roles.set(payload.role_ids)

    # 天赋人权
    enforcer.load_policy()
    enforcer.add_policy(u.username, f"user:{u.username}:password", "x")
    enforcer.add_policy(u.username, f"user:{u.username}:me", "x")

    base = UserBase.from_orm(u)
    out = UserCreateOut(
        id=u.id,
        username=u.username,
        dept_id=u.dept_id,
        role_ids=[r.id for r in u.roles.all()],
        **base.dict(),
    )
    return out


def get_all_subdepartments(dept_id):
    """递归获取部门及其所有子部门的ID"""

    department_ids = [dept_id]
    subdepartments = Department.objects.filter(parent_id=dept_id)

    for subdept in subdepartments:
        department_ids.extend(get_all_subdepartments(subdept.id))

    return department_ids


@router.get(
    "",
    response=list[UserListOut],
    auth=AuthBearer([("sys:user:edit", "x")]),
)
@api_paginate
def get_user_list(
    request, keywords: str = None, status: int = None, dept_id: int = None
):
    """获取用户列表"""

    user_list: list[UserListOut] = []

    users = User.objects.all()

    if keywords:
        users = users.filter(
            Q(name__icontains=keywords)
            | Q(nickname__icontains=keywords)
            | Q(mobile__icontains=keywords)
        )

    if status:
        users = users.filter(status=status)

    if dept_id:
        # 获取当前部门及其所有子部门的ID
        department_ids = get_all_subdepartments(dept_id)
        users = users.filter(dept_id__in=department_ids)

    users = users.all()

    for u in users:
        base = UserBase.from_orm(u)
        user_list.append(
            UserListOut(
                id=u.id,
                username=u.username,
                role_names=[r.name for r in u.roles.all()],
                dept_name=u.dept.name,
                create_time=u.create_time,
                **base.dict(),
            )
        )

    return user_list


@router.get(
    "/me",
    response=UserLoginInfoOut,
    auth=AuthBearer(
        [
            ("sys:user:edit", "x"),
            ("user:{username}:me", "x"),
        ]
    ),
)
@api_schema
def get_user_login_info(request):
    """获取用户登陆信息"""

    me = get_object_or_404(User, id=request.auth["id"])

    # 记载持久层策略
    enforcer.load_policy()
    roles = me.roles.all()
    perms: list[str] = []
    for r in roles:
        perms += [p[1] for p in enforcer.get_filtered_policy(0, r.code)]
    perms = list(set(perms))

    return UserLoginInfoOut(
        id=me.id,
        nickname=me.nickname,
        avatar=me.avatar,
        role_names=[r.code for r in me.roles.all()],
        perms=perms,
    )


@router.get(
    "/{user_id}",
    response=UserCreateOut,
    auth=AuthBearer([("sys:user:edit", "x")]),
)
@api_schema
def get_user_info(request, user_id: int):
    """获取用户信息接口"""

    u = get_object_or_404(User, id=user_id)

    base = UserBase.from_orm(u)
    out = UserCreateOut(
        id=u.id,
        username=u.username,
        dept_id=u.dept_id,
        role_ids=[r.id for r in u.roles.all()],
        **base.dict(),
    )
    return out


@router.put(
    "/{user_id}",
    response=UserCreateOut,
    auth=AuthBearer([("sys:user:edit", "x")]),
)
@api_schema
def update_user_info(request, user_id: int, payload: UserUpdateIn):
    """修改用户信息"""

    u = get_object_or_404(User, id=user_id)
    for k, v in payload.dict(exclude={"role_ids": True}).items():
        setattr(u, k, v)
    u.save()
    u.roles.set(payload.role_ids)

    base = UserBase.from_orm(u)
    out = UserCreateOut(
        id=u.id,
        username=u.username,
        dept_id=u.dept_id,
        role_ids=[r.id for r in u.roles.all()],
        **base.dict(),
    )
    return out


@router.patch(
    "/{user_id}/password",
    response=str,
    auth=AuthBearer([("sys:user:edit", "x"), ("user:{username}:password", "x")]),
)
@api_schema
def change_password(request, user_id: int, payload: UserPasswordIn):
    """修改密码"""

    u = get_object_or_404(User, id=user_id)
    u.password = get_password(payload.password)
    u.save()
    return "OK"


@router.delete(
    "/{user_id}",
    response=str,
    auth=AuthBearer([("sys:user:delete", "x")]),
)
@api_schema
def delete_user(request, user_id: int):
    """删除用户"""

    u = get_object_or_404(User, id=user_id)
    u.delete()

    # 剥夺人权
    enforcer.load_policy()
    enforcer.remove_filtered_policy(0, u.username)

    return "Ok"
