from datetime import datetime, timezone

from django.shortcuts import get_object_or_404
from ninja import Router

from apps.sys.models import Menu, Role
from apps.sys.schemas import (
    MenuType,
    RoleIn,
    RoleMenuIn,
    RoleOptionOut,
    RoleOut,
    RoleUpdateIn,
)
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from casbin_adapter.enforcer import enforcer

from utils.schema.paginate import api_paginate


router = Router()


@router.post(
    "",
    response=RoleOut,
    auth=AuthBearer([("sys:role:add", "x")]),
)
@api_schema
def create_roles(request, payload: RoleIn):
    """创建角色接口"""

    r = Role(create_time=datetime.now(timezone.utc), **payload.dict())
    r.save()
    return r


@router.get(
    "",
    response=list[RoleOut],
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_paginate
def get_role_info_list(request):
    """角色列表接"""

    return Role.objects.all()


@router.get(
    "/options",
    response=list[RoleOptionOut],
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def get_role_option_list(request):
    """角色选项列表"""

    return Role.objects.all()


@router.get(
    "/{role_id}",
    response=RoleOut,
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def get_role_info(request, role_id: int):
    """角色信息接口"""

    return get_object_or_404(Role, id=role_id)


@router.put(
    "/{role_id}",
    response=RoleOut,
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def update_role_info(request, role_id: int, payload: RoleUpdateIn):
    """修改角色接口"""

    r = get_object_or_404(Role, id=role_id)
    r.name = payload.name
    r.status = payload.status
    r.sort = payload.status
    r.save()
    return r


@router.patch(
    "/{role_id}",
    response=RoleOut,
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def update_role_status(reques, role_id: int, status: int):
    """修改角色状态"""

    r = get_object_or_404(Role, id=role_id)
    r.status = status
    r.save()
    return r


@router.put(
    "/{role_id}/menus",
    response=list[int],
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def update_role_menus(request, role_id: int, payload: RoleMenuIn):
    """分配菜单权限"""

    r = get_object_or_404(Role, id=role_id)
    menus = Menu.objects.filter(id__in=payload.menus).all()
    added_menus = []

    # 删除旧权限
    enforcer.load_policy()
    enforcer.remove_filtered_policy(0, r.code)

    for m in menus:
        if m.menu_type == MenuType.BUTTON.value and m.perm:
            # 给角色添加新权限
            enforcer.add_policy(r.code, m.perm, "x")
        added_menus.append(m.id)

    # 保存菜单列表
    r.menu_set.set(added_menus)

    return added_menus


@router.get(
    "/{role_id}/menus",
    response=list[int],
    auth=AuthBearer([("sys:role:edit", "x")]),
)
@api_schema
def get_role_menus(request, role_id: int):
    """获取角色菜单权限"""

    r = get_object_or_404(Role, id=role_id)
    return [m.id for m in r.menu_set.all()]


@router.delete(
    "/{role_id}",
    response=str,
    auth=AuthBearer([("sys:role:delete", "x")]),
)
@api_schema
def delete_role(request, role_id: int):
    """删除角色"""

    r = get_object_or_404(Role, id=role_id)

    # 加载权限
    enforcer.load_policy()
    enforcer.remove_filtered_policy(0, r.code)

    r.delete()
    return "Ok"
