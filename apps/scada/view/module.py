from datetime import datetime

from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.scada.models import Module
from apps.scada.schema.module import ModuleIn, ModuleInfoOut, ModuleOptionOut, ModuleOut, ModuleUpdateIn
from apps.scada.utils.grm.client import GrmError
from apps.scada.utils.pool import get_grm_client
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post(
    "",
    response=ModuleOut,
    auth=AuthBearer([("scada:module:create", "x")]),
)
@api_schema
def create_module(request, payload: ModuleIn):
    """创建GRM模块接口"""

    module = Module(updated_at=datetime.now(), **payload.dict())
    module.save()
    return module


@router.get(
    "/options",
    response=list[ModuleOptionOut],
    auth=AuthBearer([("scada:module:list", "x")]),
)
@api_schema
def get_module_option_list(request):
    """获取选项列表"""

    return Module.objects.all()


@router.get(
    "/{module_id}",
    response=ModuleInfoOut,
    auth=AuthBearer([("scada:module:info", "x")]),
)
@api_schema
def get_module_info(request, module_id: int):
    """获取模块信息"""

    module = get_object_or_404(Module, id=module_id)

    # 获取巨控信息
    out = ModuleInfoOut.from_orm(module)
    try:
        client = get_grm_client(module)
        out.info = client.info()
    except Exception:
        # 模块信息获取不到
        pass
    return out


@router.get(
    "",
    response=list[ModuleOut],
    auth=AuthBearer([("scada:module:list", "x")]),
)
@api_paginate
def get_module_list(request, keywords: str = None):
    """获取模块列表"""

    modules = Module.objects.all()

    if keywords:
        modules = modules.filter(
            Q(name__icontains=keywords) | Q(module_number__icontains=keywords)
        )
    return modules.all()


@router.put(
    "/{module_id}",
    response=ModuleOut,
    auth=AuthBearer([("scada:module:update", "x")]),
)
@api_schema
def update_grm(request, module_id: int, payload: ModuleUpdateIn):
    """更新模块信息"""

    module = get_object_or_404(Module, id=module_id)
    module.name = payload.name
    module.module_secret = payload.module_secret
    module.module_url = payload.module_url
    module.save()
    return module


@router.delete(
    "/{module_id}",
    response=str,
    auth=AuthBearer([("scada:module:delete", "x")]),
)
@api_schema
def delete_grm(request, module_id: int):
    """删除模块"""

    module = get_object_or_404(Module, id=module_id)
    module.delete()
    return "Ok"
