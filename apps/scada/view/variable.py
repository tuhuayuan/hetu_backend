
import requests
from django.conf import settings
from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from ninja import Query, Router
from ninja.errors import HttpError
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    delete_from_gateway,
    push_to_gateway,
)

from apps.scada.models import Module, Variable
from apps.scada.schema.variable import (
    ReadValueIn,
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
from apps.scada.utils.promql import PrometheusQueryError, query_prometheus
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.get(
    "/{site_id}/variable/{variable_id}/range",
    response=ReadValueOut,
    auth=AuthBearer(
        [
            ("scada:variable:read", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def read_range(
    request,
    site_id: int,
    variable_id: int,
    offset: str = Query(default=None, regex=r"^\d+[mshd]$"),
    duration: str = Query(default="1h", regex=r"^\d+[msh]$"),
):
    var = get_object_or_404(Variable, id=variable_id, module__site_id=site_id)
    query_str = "grm_" + var.module.module_number + "_gauge"
    query_str += '{name="' + var.name + '"}'
    query_str += f"[{duration}]"

    # 可选的偏移参数
    if offset:
        query_str += f" offset {offset}"

    try:
        query_data = query_prometheus(query_str)
    except PrometheusQueryError as e:
        raise HttpError(500, f"Prometheus Query Error: {e}")
    except requests.RequestException as e:
        raise HttpError(500, f"Request Error: {e}")

    # 格式参考 https://prometheus.io/docs/prometheus/latest/querying/api/#expression-query-result-formats
    values: list[ReadValueOut.Value] = []
    out = ReadValueOut.from_orm(var)
    for result in query_data["data"]["result"]:
        for value_set in result["values"]:
            values.append(
                ReadValueOut.Value(timestamp=value_set[0], value=float(value_set[1]))
            )
        break
    out.values = values
    return out


@router.post(
    "/{site_id}/variable/values",
    response=list[ReadValueOut],
    auth=AuthBearer(
        [
            ("scada:variable:read", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def read_values(
    request,
    site_id: int,
    payload: ReadValueIn,
):
    """批量读取变量值"""

    vars = Variable.objects.filter(id__in=payload.variable_ids, module__site_id=site_id)

    # 获取给定 variable_ids 下每个 module_id 中的变量列表
    grouped_vars = (
        vars.select_related("module")
        .values("module_id", "module__module_number")
        .distinct()
    )

    outlist: list[ReadValueOut] = []

    # 数据是按模块存储，所以变量按模块获取
    for entry in grouped_vars:
        module_id = entry["module_id"]
        module_number = entry["module__module_number"]
        module_vars = vars.filter(module_id=module_id)

        query_str = "grm_" + module_number + "_gauge"
        query_str += '{name=~"' + "|".join([v.name for v in module_vars]) + '"}'

        try:
            query_data = query_prometheus(query_str)
        except PrometheusQueryError as e:
            raise HttpError(500, f"Prometheus Query Error: {e}")
        except requests.RequestException as e:
            raise HttpError(500, f"Request Error: {e}")

        # 构建输出结构
        for v in vars:
            out = ReadValueOut.from_orm(v)
            for result in query_data["data"]["result"]:
                if result["metric"]["name"] == v.name:
                    value = ReadValueOut.Value(
                        timestamp=result["value"][0], value=float(result["value"][1])
                    )
                    out.values.append(value)
                    break
            outlist.append(out)

    return outlist


@router.post(
    "/{site_id}/module/{module_id}/variable",
    response=VariableOut,
    auth=AuthBearer(
        [
            ("scada:variable:add", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def create_variable(
    request,
    site_id: int,
    module_id: int,
    payload: VariableIn,
):
    """创建变量"""

    module = get_object_or_404(Module, id=module_id, site_id=site_id)
    v = Variable(module_id=module.id, **payload.dict())
    v.save()
    v.site_id=site_id
    return v


@router.get(
    "/{site_id}/module/{module_id}/variable/options",
    response=list[VariableOptionOut],
    auth=AuthBearer(
        [
            ("scada:variable:edit", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_variable_option_list(
    request,
    site_id: int,
    module_id: int,
    group: str = None,
):
    """获取模块的变量选项"""

    vs = Variable.objects.filter(module_id=module_id, module__site_id=site_id)

    if group:
        vs = vs.filter(group=group)

    return vs.all()


@router.get(
    "/{site_id}/module/{module_id}/variable/groups",
    response=list[str],
    auth=AuthBearer(
        [
            ("scada:variable:edit", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_variable_group_list(
    request,
    site_id: int,
    module_id: int,
    keywords: str = None,
):
    """获取变量组"""

    gs = Variable.objects.filter(module_id=module_id, module__site_id=site_id)

    if keywords:
        gs = gs.filter(Q(group__icontains=keywords))

    return gs.values("group").distinct().values_list("group", flat=True)


@router.put(
    "/{site_id}/module/{module_id}/variable/{variable_id}",
    response=VariableOut,
    auth=AuthBearer(
        [
            ("scada:variable:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def update_variable(
    request,
    site_id: int,
    module_id: int,
    variable_id: int,
    payload: VariableUpdateIn,
):
    """更新变量信息"""

    v = get_object_or_404(
        Variable, id=variable_id, module_id=module_id, module__site_id=site_id
    )
    v.type = payload.type
    v.rw = payload.rw
    v.details = payload.details
    v.save()
    v.site_id =site_id
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
    "/{site_id}/variable/values",
    response=list[WriteValueOut],
    auth=AuthBearer(
        [
            ("scada:variable:write", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def update_variable_values(
    request,
    site_id: int,
    payload: list[WriteValueIn],
):
    """写模块变量接口"""

    outlist: list[WriteValueOut] = []

    # 逐个写入
    for p in payload:
        out = WriteValueOut(id=p.id)
        var = Variable.objects.filter(
            id=p.id,
            module__site_id=site_id,
        ).first()

        if not var:
            out.error = 404
        elif not var.rw:
            out.error = 422
        elif not var.local:
            # 获取客户端
            client = get_grm_client(var.module)

            grm_write_list = [
                GrmVariable(
                    module_number=var.module.module_number,
                    type=var.type,
                    name=var.name,
                    value=p.value,
                    group=var.group,
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
                write_local_var(var, p)
            except Exception as e:
                out.error = 503

        outlist.append(out)

    return outlist


@router.get(
    "/{site_id}/module/{module_id}/variable/{variable_id}",
    response=VariableOut,
    auth=AuthBearer(
        [
            ("scada:variable:edit", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_variable_info(
    request,
    site_id: int,
    module_id: int,
    variable_id: int,
):
    """获取变量信息"""

    var = get_object_or_404(
        Variable, id=variable_id, module_id=module_id, module__site_id=site_id
    )
    var.site_id = site_id
    return VariableOut.from_orm(var)


@router.get(
    "/{site_id}/module/{module_id}/variable",
    response=list[VariableOut],
    auth=AuthBearer(
        [
            ("scada:variable:edit", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_paginate
def get_variable_list(
    request, site_id: int, module_id: int, keywords: str = None, group: str = None
):
    """列出模块的所有变量"""
    fields = [field.name for field in Variable._meta.get_fields()]
    fields.append("module__site_id")
    vars = Variable.objects.filter(
        module_id=module_id,
        module__site_id=site_id,
    ).annotate(site_id=F("module__site_id"))

    if group:
        vars = vars.filter(group=group)

    if keywords:
        vars = vars.filter(Q(name__icontains=keywords))

    return vars.all()


@router.delete(
    "/{site_id}/module/{module_id}/variable/{variable_id}",
    response=str,
    auth=AuthBearer(
        [
            ("scada:variable:delete", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def delete_variable(request, site_id: int, module_id: int, variable_id: int):
    """删除变量接口"""

    var = get_object_or_404(
        Variable, id=variable_id, module_id=module_id, module__site_id=site_id
    )

    # 本地变量要从pushgateway删除
    if var.local:
        labels = {"name": var.name, "type": var.type, "local": "true"}

        delete_from_gateway(
            settings.PUSHGATEWAY_URL,
            job="grm_local",
            grouping_key=labels,
        )

    var.delete()
    return "OK"
