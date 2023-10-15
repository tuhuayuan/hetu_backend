from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.errors import HttpError
from prometheus_client import CollectorRegistry, Gauge, delete_from_gateway, push_to_gateway

from apps.scada.models import Module, Variable
from apps.scada.schema.variable import (
    VariableIn,
    VariableOptionOut,
    VariableOut,
    ReadValueOut,
    VariableUpdateIn,
    WriteValueIn,
    WriteValueOut,
)
from apps.scada.utils.grm.schemas import GrmVariable
from apps.scada.utils.pool import get_grm_client
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.get(
    "/values",
    response=list[ReadValueOut],
    auth=AuthBearer([("scada:variable:values:read", "x")]),
)
@api_schema
def get_variable_values(
    request,
    variable_ids: list[int] = Query(default=[]),
    offset: str = Query(default=None, regex=r"^\d+[mshd]$"),
    duration: str = Query(default=None, regex=r"^\d+[msh]$"),
):
    """批量读取变量值"""

    vs = Variable.objects.filter(id__in=variable_ids).all()
    outlist: list[ReadValueOut] = []

    for v in vs:
        query_str = "grm_" + v.module.module_number + "_gauge"
        query_str += '{name="' + v.name + '"}'

        if duration:
            query_str += f"[{duration}]"

        if offset:
            query_str += f" offset {offset}"

        # 记得编码url参数
        query_params = urlencode({"query": query_str})
        query_resp = requests.get(
            f"{settings.PROMETHEUS_URL}/api/v1/query?{query_params}",
            timeout=(3, 5),
        )

        if query_resp.status_code != 200:
            raise HttpError(500, f"tsdb error {query_resp.status_code}")

        query_data = query_resp.json()
        if query_data["status"] != "success":
            raise HttpError(500, f'tsdb error {query_data["error"]}')

        # 格式参考 https://prometheus.io/docs/prometheus/latest/querying/api/#expression-query-result-formats
        result_type = query_data["data"]["resultType"]

        # 单个输出值
        out = ReadValueOut.from_orm(v)

        # 遍历查询结果
        for result in query_data["data"]["result"]:
            if result_type == "vector":
                # vector类型每个metric只有一个值
                value = ReadValueOut.Value(
                    timestamp=result["value"][0], value=float(result["value"][1])
                )
                out.values = [value]
            else:
                # matrix类型每个metric有多个值
                values: list[ReadValueOut.Value] = []

                for value_set in result["values"]:
                    values.append(
                        ReadValueOut.Value(
                            timestamp=value_set[0], value=float(value_set[1])
                        )
                    )
                out.values = values
            break

        outlist.append(out)

    return outlist


@router.post(
    "",
    response=VariableOut,
    auth=AuthBearer([("scada:variable:create", "x")]),
)
@api_schema
def create_variable(request, payload: VariableIn):
    """创建变量"""

    v = Variable(**payload.dict())
    v.save()
    return v


@router.get(
    "/options",
    response=list[VariableOptionOut],
    auth=AuthBearer([("scada:variable:list", "x")]),
)
@api_schema
def get_variable_option_list(request, module_id: int):
    """获取模块的变量选项"""

    return Variable.objects.filter(module_id=module_id)


@router.put(
    "/{variable_id}",
    response=VariableOut,
    auth=AuthBearer([("scada:variable:update", "x")]),
)
def update_variable(request, variable_id: int, payload: VariableUpdateIn):
    """更新变量信息"""

    v = get_object_or_404(Variable, id=variable_id)
    v.type = payload.type
    v.rw = payload.rw
    v.details = payload.details
    v.save()
    return v


def write_local_var(variable: Variable, payload: WriteValueIn):
    """通过pushgateway实现模块手动设置的本地的变量"""

    # 创建一个 CollectorRegistry 对象
    registry = CollectorRegistry()

    # 创建一个 Gauge 指标
    gauge = Gauge(
        f"grm_{variable.module.module_number}_gauge",
        variable.details,
        registry=registry,
    )

    # 设置指标的值
    gauge.set(payload.value)

    # 设置标签
    labels = {"name": variable.name, "type": variable.type, "local": "true"}

    # 写入
    push_to_gateway(
        settings.PUSHGATEWAY_URL,
        job="grm_local",
        registry=registry,
        grouping_key=labels,
    )


@router.put(
    "/values",
    response=list[WriteValueOut],
    auth=AuthBearer([("scada:variable:values:write", "x")]),
)
def update_variable_values(request, payload: list[WriteValueIn]):
    """写模块变量接口"""

    vs = Variable.objects.filter(
        id__in=[i.id for i in payload],
        rw=True,
    )
    outlist: list[WriteValueOut] = []

    # 逐个写入
    for p in payload:
        out = WriteValueOut(id=p.id)
        v = Variable.objects.filter(id=p.id).first()

        if not v:
            out.error = 404
        elif not v.rw:
            out.error = 422
        elif not v.local:
            # 获取客户端
            client = get_grm_client(v.module)

            grm_write_list = [
                GrmVariable(
                    module_number=v.module.module_number,
                    type=v.type,
                    name=v.name,
                    value=p.value,
                    group=v.group,
                )
            ]
            try:
                # 写远程GRM设备
                client.write(grm_write_list)
                out.error = grm_write_list[0].write_error
            except:
                out.error = 503
        else:
            # 本地pushgateway变量
            try:
                write_local_var(v, p)
            except Exception as e:
                out.error = 503

        outlist.append(out)

    return outlist


@router.get(
    "/{variable_id}",
    response=VariableOut,
    auth=AuthBearer([("scada:variable:info", "x")]),
)
@api_schema
def get_variable_info(request, variable_id: int):
    """获取变量信息"""

    return get_object_or_404(Variable, id=variable_id)


@router.get(
    "",
    response=list[VariableOut],
    auth=AuthBearer([("scada:variable:list", "x")]),
)
@api_paginate
def get_variable_list(request, module_id: int = None, keywords: str = None):
    """列出模块的所有变量"""
    vs = Variable.objects.all()

    if module_id:
        vs = vs.filter(module_id=module_id)

    if keywords:
        vs = vs.filter(Q(name__icontains=keywords))

    return vs.all()


@router.delete(
    "/{variable_id}",
    response=str,
    auth=AuthBearer([("scada:variable:delete", "x")]),
)
@api_schema
def delete_variable(request, variable_id: int):
    """删除变量接口"""

    v = get_object_or_404(Variable, id=variable_id)

    # 本地变量要从pushgateway删除
    if v.local:
        labels = {"name": v.name, "type": v.type, "local": "true"}

        delete_from_gateway(
            settings.PUSHGATEWAY_URL,
            job="grm_local",
            grouping_key=labels,
        )

    v.delete()
    return "OK"
