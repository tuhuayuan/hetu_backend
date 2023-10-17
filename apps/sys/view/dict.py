from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.sys.models import DictData, DictType
from apps.sys.schemas import (
    DictDataIn,
    DictDataOptionOut,
    DictDataOut,
    DictTypeIn,
    DictTypeOut,
)
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post(
    "/type",
    response=DictTypeOut,
    auth=AuthBearer([("sys:dict:type:create", "x")]),
)
@api_schema
def create_dicttype(request, payload: DictTypeIn):
    """创建字典类型"""

    dt = DictType(**payload.dict())
    dt.save()
    return dt


@router.get(
    "/type",
    response=list[DictTypeOut],
    auth=AuthBearer([("sys:dict:type:list", "x")]),
)
@api_paginate
def list_dicttype(request, keywords: str = None):
    """获取字典类型列表"""

    dts = DictType.objects.all()

    if keywords:
        dts = dts.filter(Q(name__icontains=keywords) | Q(code__icontains=keywords))

    return dts


@router.get(
    "/type/{type_id}",
    response=DictTypeOut,
    auth=AuthBearer([("sys:dict:type:info", "x")]),
)
@api_schema
def get_dicttype(request, type_id: int):
    """获取字典类型信息"""

    return get_object_or_404(DictType, id=type_id)


@router.put(
    "/type/{type_id}",
    response=DictTypeOut,
    auth=AuthBearer([("sys:dict:type:update", "x")]),
)
@api_schema
def update_dicttype(request, type_id: int, payload: DictTypeIn):
    """更新字典类型信息"""

    dt = get_object_or_404(DictType, id=type_id)
    dt.name = payload.name
    dt.code = payload.code
    dt.status = payload.status
    dt.remark = payload.remark
    dt.save()
    return dt


@router.delete(
    "/type/{type_id}",
    response=str,
    auth=AuthBearer([("sys:dict:type:delete", "x")]),
)
@api_schema
def delete_dicttype(request, type_id: int):
    """删除字典类型"""

    dt = get_object_or_404(DictType, id=type_id)
    dt.delete()
    return "OK"


@router.post(
    "/data",
    response=DictDataOut,
    auth=AuthBearer([("sys:dict:data:create", "x")]),
)
@api_schema
def create_dictdata(request, payload: DictDataIn):
    """创建字典数据"""

    dd = DictData(**payload.dict())
    dd.save()
    return dd


@router.get(
    "/data",
    response=list[DictDataOut],
    auth=AuthBearer([("sys:dict:data:list", "x")]),
)
@api_paginate
def get_dictdata_list(request, type_code: str = None, keywords: str = None):
    """获取字典数据列表"""

    dds = DictData.objects.all()

    if type_code:
        dds = dds.filter(type_code=type_code)

    if keywords:
        dds = dds.filter(Q(name__icontains=keywords) | Q(value__icontains=keywords))

    return dds.all()


@router.get(
    "/data/options",
    response=list[DictDataOptionOut],
    auth=AuthBearer([("sys:dict:data:options", "x")]),
)
@api_schema
def get_dictdata_option_list(request, type_code: str):
    """获取字典选项列表"""

    return DictData.objects.filter(type_code=type_code).all()


@router.get(
    "/data/{data_id}",
    response=DictDataOut,
    auth=AuthBearer([("sys:dict:data:info", "x")]),
)
@api_schema
def get_dictdata(request, data_id: int):
    """获取字典数据信息"""

    return get_object_or_404(DictData, id=data_id)


@router.put(
    "/data/{data_id}",
    response=DictDataOut,
    auth=AuthBearer([("sys:dict:data:update", "x")]),
)
@api_schema
def update_dictdata(request, data_id: int, payload: DictDataIn):
    """更新字典数据"""

    dd = get_object_or_404(DictData, id=data_id)
    dd.name = payload.name
    dd.value = payload.value
    dd.status = payload.status
    dd.sort = payload.sort
    dd.remark = payload.remark
    dd.type_code = payload.type_code
    dd.save()
    return dd


@router.delete(
    "/data/{data_id}",
    response=str,
    auth=AuthBearer([("sys:dict:data:delete", "x")]),
)
@api_schema
def delete_dictdata(request, data_id: int):
    """删除字典数据"""

    dd = get_object_or_404(DictData, id=data_id)
    dd.delete()
    return "Ok"
