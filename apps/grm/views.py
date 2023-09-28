import threading
from datetime import datetime
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db import IntegrityError
from ninja import Query, Router
from ninja.errors import HttpError
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from apps.grm.models import GrmModule, GrmModuleVar
from apps.grm.schemas import (
    CreateModuleIn,
    CreateModuleVarIn,
    GetModule,
    GetModuleInfo,
    GetModuleVar,
    ReadValue,
    ReadValueIn,
    UpdateModuleIn,
    WriteValueIn,
    WriteValueOut,
)
from utils.grm.client import GrmClient, GrmError
from utils.grm.schemas import ModuleVar
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()

# 每个线程维护自己的连接池
grm_pool_local = threading.local()


def get_grm_client(grm: GrmModule) -> GrmClient:
    """缓存使用过的grm客户端"""

    key = (
        grm.module_id,
        grm.module_secret,
        grm.module_url,
    )

    if not hasattr(grm_pool_local, "grm_pool"):
        pool: dict[
            tuple[
                str,
                str,
                str,
            ],
            GrmClient,
        ] = {}
        grm_pool_local.grm_pool = pool
    else:
        pool = grm_pool_local.grm_pool

    if key in pool:
        return pool[key]
    else:
        client = GrmClient(grm.module_id, grm.module_secret, grm.module_url)
        client.connect()

        pool[key] = client
        return client


def write_local_var(model: GrmModuleVar, req: WriteValueIn):
    """通过pushgateway实现模块手动设置的本地的变量"""

    # 创建一个 CollectorRegistry 对象
    registry = CollectorRegistry()

    # 创建一个 Gauge 指标
    gauge = Gauge(f"grm_{model.module_id}_gauge", model.details, registry=registry)

    # 设置指标的值
    gauge.set(req.value)

    # 设置标签
    labels = {"name": model.name, "type": model.type, "local": "true"}

    # 写入
    push_to_gateway(
        settings.PROMETHUES_PUSHGATEWAY,
        job="grm_local",
        registry=registry,
        grouping_key=labels,
    )


@router.get("/{module_id}/vars", response=list[GetModuleVar])
@api_paginate
def list_vars(request, module_id: str):
    """列出模块的所有变量"""

    module = GrmModule.objects.filter(module_id=module_id).first()

    if not module:
        raise HttpError(404, f"模块{module_id}不存在")

    return module.vars.all()


@router.post("/{module_id}/vars", response=GetModuleVar)
@api_schema
def create_var(request, module_id: str, data: CreateModuleVarIn):
    """创建变量接口"""

    module = GrmModule.objects.filter(module_id=module_id).first()

    if not module:
        raise HttpError(404, f"模块{module_id}不存在")

    try:
        var_model = GrmModuleVar.objects.create(module_id=module_id, **data.dict())
    except IntegrityError:
        raise HttpError(500, f"变量({data.name})已经存在于模块({module_id})")

    return var_model


@router.get("/{module_id}/vars/{var_name}", response=GetModuleVar)
@api_schema
def get_var(request, module_id: str, var_name: str):
    """获取变量信息"""

    var_model = GrmModuleVar.objects.filter(module_id=module_id, name=var_name).first()

    if not var_model:
        raise HttpError(404, f"变量({var_name})或者模块({module_id})不存在")

    return var_model


@router.delete("/{module_id}/vars/{var_name}", response=str)
@api_schema
def delete_var(request, module_id: str, var_name: str):
    """删除变量接口"""

    var_model = GrmModuleVar.objects.filter(module_id=module_id, name=var_name).first()

    if not var_model:
        raise HttpError(404, f"变量({var_name})或者模块({module_id})不存在")

    var_model.delete()
    return "OK"


@router.post("/{module_id}/reader", response=list[ReadValue])
@api_schema
def read_values(
    request,
    module_id: str,
    var_list: list[ReadValueIn],
    offset: str = Query(default="", regex=r"^\d+[mshd]$"),
    duration: str = Query(default="", regex=r"^\d+[msh]$"),
):
    """读取变量接口"""

    module = GrmModule.objects.filter(module_id=module_id).first()
    if not module:
        raise HttpError(404, f"模块({module_id})不存在")

    resp: list[ReadValue] = []

    for module_var in var_list:
        var_model = module.vars.filter(name=module_var.name).first()
        if not var_model:
            # 设置读取错误状态
            resp.append(ReadValue(name=module_var.name, type="", error=404))
            continue
        else:
            read_value = ReadValue(
                module_id=module_id, name=var_model.name, type=var_model.type
            )

        query_str = "grm_" + module_id + "_gauge"
        query_str += '{name="' + module_var.name + '"}'

        if duration:
            query_str += f"[{duration}]"

        if offset:
            query_str += f" offset {offset}"

        # 记得编码url参数
        query_params = urlencode({"query": query_str})
        query_resp = requests.get(
            f"{settings.PROMETHEUS_URL}/api/v1/query?{query_params}"
        )

        if query_resp.status_code != 200:
            raise HttpError(503, f"tsdb error {query_resp.status_code}")

        query_data = query_resp.json()
        if query_data["status"] != "success":
            raise HttpError(503, f'tsdb error {query_data["error"]}')

        # 格式参考 https://prometheus.io/docs/prometheus/latest/querying/api/#expression-query-result-formats
        result_type = query_data["data"]["resultType"]

        # 遍历查询结果
        for result in query_data["data"]["result"]:
            if result_type == "vector":
                # vector类型每个metric只有一个值
                value = ReadValue.Value(
                    timestamp=result["value"][0], value=float(result["value"][1])
                )
                read_value.values = [value]
            else:
                # matrix类型每个metric有多个值
                values: list[ReadValue.Value] = []

                for value_set in result["values"]:
                    values.append(
                        ReadValue.Value(
                            timestamp=value_set[0], value=float(value_set[1])
                        )
                    )
                read_value.values = values
            break

        resp.append(read_value)

    return resp


@router.post("/{module_id}/writer", response=list[WriteValueOut])
def write_values(request, module_id: str, var_list: list[WriteValueIn]):
    """写模块变量接口"""

    module = GrmModule.objects.filter(module_id=module_id).first()
    if not module:
        raise HttpError(404, f"模块({module_id})不存在")

    # 获取客户端
    client = get_grm_client(module)

    resp: list[WriteValueOut] = []

    for var_write in var_list:
        var_model = module.vars.filter(name=var_write.name).first()
        if not var_model:
            # 设置读取错误状态
            resp.append(WriteValueOut(name=var_write.name, error=404))
            continue
        elif not var_model.rw:
            resp.append(WriteValueOut(name=var_write.name, error=405))
            continue
        else:
            write_value = WriteValueOut(name=var_model.name)

        if not var_model.local:
            # 远程GRM设备
            grm_write_list = [
                ModuleVar(
                    module_id=module_id,
                    type=var_model.type,
                    name=var_write.name,
                    value=var_write.value,
                )
            ]
            try:
                client.write(grm_write_list)
                write_value.error = grm_write_list[0].write_error
            except:
                write_value.error = -99

        else:
            # 本地pushgateway变量
            try:
                write_local_var(var_model, var_write)
            except Exception as e:
                print(e)
                write_value.error = -100

        resp.append(write_value)
    return resp


@router.get("/", response=list[GetModule])
@api_paginate
def list_modules(request):
    """获取模块信息列表接口"""

    return GrmModule.objects.all()


@router.get("/{module_id}", response=GetModuleInfo)
@api_schema
def get_module(request, module_id: str):
    """获取单个模块信息接口"""

    module = GrmModule.objects.filter(module_id=module_id).first()
    if not module:
        raise HttpError(404, f"模块{module_id}不存在")

    # 获取巨控信息
    client = get_grm_client(module)
    resp = GetModuleInfo.from_orm(module)
    try:
        resp.info = client.info()
    except GrmError:
        # 模块信息获取不到
        pass
    return resp


@router.post("/", response=GetModule)
@api_schema
def create_module(request, data: CreateModuleIn):
    """创建GRM模块接口"""

    try:
        module = GrmModule.objects.create(updated_at=datetime.now(), **data.dict())
    except IntegrityError:
        raise HttpError(500, "模块已存在")

    return module


@router.post("/{module_id}", response=GetModule)
@api_schema
def update_grm(request, module_id, data: UpdateModuleIn):
    """更新接口"""

    module = GrmModule.objects.filter(module_id=module_id).first()
    if not module:
        raise HttpError(404, f"模块{module_id}不存在")

    module.name = data.name
    module.module_secret = data.module_secret
    module.module_url = data.module_url

    # 保存
    try:
        module.save()
    except Exception as e:
        raise HttpError(500, f"保存失败: {e}")

    return module


@router.delete("/{module_id}", response=str)
@api_schema
def delete_grm(request, module_id):
    module = GrmModule.objects.filter(module_id=module_id).first()
    if not module:
        raise HttpError(404, f"模块{module_id}不存在")

    try:
        module.delete()
    except Exception as e:
        raise HttpError(500, f"删除失败: {e}")

    return "OK"
