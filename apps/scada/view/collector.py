import fcntl
import os
import time
from string import Template
from xmlrpc.client import ServerProxy
from django.shortcuts import get_object_or_404
from django.conf import settings
from ninja import Router
from ninja.errors import HttpError
from apps.scada.models import Collector, Module

from apps.scada.schema.collector import (
    CollectorIn,
    CollectorOut,
    CollectorStatusIn,
)
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()

rpc = ServerProxy(settings.SUPERVISOR_XMLRPC_URL)


supervisor_tpl = Template(
    """
[program:$process_name]
command=$command
environment=PYTHONPATH=/app/src,MODULE_NUMBER="$module_number",MODULE_SECRET="$module_secret",MODULE_URL="$module_url",RANDOM_PORT=$port,HOST="$host",ADVERTISE="$advertise"
autorestart=unexpected
"""
)


def supervisor_update():
    """实现supervisorctl的update命令
    参考supervisorctl的源码实现, 只是异常交给上层处理
    """

    result = rpc.supervisor.reloadConfig()
    added, changed, removed = result[0]

    for gname in removed:
        try:
            rpc.supervisor.stopProcessGroup(gname)
            rpc.supervisor.removeProcessGroup(gname)
        except:
            continue

    for gname in changed:
        try:
            rpc.supervisor.stopProcessGroup(gname)
            rpc.supervisor.removeProcessGroup(gname)
            rpc.supervisor.addProcessGroup(gname)
        except:
            continue

    for gname in added:
        try:
            rpc.supervisor.addProcessGroup(gname)
        except:
            continue


def get_proccess_name(collector: Collector):
    """获取进程名称"""

    return f"collector_{collector.module.module_number}"


def get_proccess_file(collector: Collector):
    """获取配置文件路径"""

    return f"{settings.SUPERVISOR_COLLECTOR_DIR}/{get_proccess_name(collector)}.conf"


def rewrite_process_config(collector: Collector) -> bool:
    """更新配置文件"""

    process_name = get_proccess_name(collector)
    file_path = get_proccess_file(collector)

    # 配置文件内容
    content = supervisor_tpl.substitute(
        process_name=process_name,
        module_number=collector.module.module_number,
        module_secret=collector.module.module_secret,
        module_url=collector.module.module_url,
        command=settings.SUPERVISOR_COLLECTOR_COMMAND,
        host=settings.SUPERVISOR_COLLECTOR_HOST,
        port=settings.SUPERVISOR_COLLECTOR_PORT,
        advertise=settings.SUPERVISOR_COLLECTOR_ADVERTISE,
    )
    # 获得文件锁
    with open(file_path, "w") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # 在这里进行其他进程不能创建文件的操作
            file.write(content)
        finally:
            # 释放文件锁
            fcntl.flock(file, fcntl.LOCK_UN)


def delete_process_config(collector: Collector):
    """删除配置"""

    file_path = get_proccess_file(collector)
    os.remove(file_path)


@router.put(
    "/{site_id}/module/{module_id}/collector",
    response=CollectorOut,
    auth=AuthBearer(
        [
            ("scada:collector:add", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def create_collector(request, site_id: int, module_id: int, payload: CollectorIn):
    """创建数据采集器器"""

    module = get_object_or_404(Module, id=module_id, site_id=site_id)

    collector, created = Collector.objects.get_or_create(module_id=module.id)
    collector.interval = payload.interval
    collector.timeout = payload.timeout
    collector.save()

    # 刷新
    rewrite_process_config(collector)

    # 更新守护进程
    try:
        supervisor_update()
    except Exception:
        raise HttpError(500, "采集器配置失败")

    return collector


def get_exporter_url(process_name: str) -> str:
    """解析日志里面的服务地址"""

    log = rpc.supervisor.tailProcessStdoutLog(process_name, 0, 255)[0]
    advertise = ""
    try:
        lines = log.splitlines()[::-1]

        for l in lines:
            if l.startswith("# ADVERTISE"):
                # 格式是这样的 # ADVERTISE 27.0.0.1:20986
                advertise = l.split(" ")[2]
                raise EOFError()
        return ""
    except:
        return advertise


def service_discover(request):
    """实现Prometheus的HTTP SD接口
    https://prometheus.io/docs/prometheus/latest/http_sd/
    """
    collectors = Collector.objects.all()
    running_list = []
    for c in collectors:
        process_name = get_proccess_name(c)

        # 获取进程状态
        try:
            info = rpc.supervisor.getProcessInfo(process_name)

            if info["statename"] == "RUNNING":
                # 加入服务发现
                running_list.append(
                    {
                        "targets": [get_exporter_url(process_name)],
                        "labels": {
                            "__scrape_interval__": f"{c.interval}s",
                            "__scrape_timeout__": f"{c.timeout}s",
                        },
                    }
                )
        except:
            # 不需要处理错误
            continue

    return 200, running_list


@router.get(
    "/{site_id}/module/{module_id}/collector",
    response=list[CollectorOut],
    auth=AuthBearer(
        [
            ("scada:collector:edit", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_collector_list(request, site_id: int, module_id: int):
    """获取列表"""

    collectors = Collector.objects.filter(module_id=module_id, module__site_id=site_id)
    outlist: list[CollectorOut] = []

    for c in collectors:
        out = CollectorOut.from_orm(c)

        # 获取运行状态
        process_name = get_proccess_name(c)
        try:
            info = rpc.supervisor.getProcessInfo(process_name)
            out.running = info["statename"] == "RUNNING"
        except:
            out.running = False

        # 获取运行地址
        if out.running:
            out.exporter_url = get_exporter_url(process_name)

        # 压入列表
        outlist.append(out)

    return outlist


@router.patch(
    "/{site_id}/module/{module_id}/collector/{collector_id}",
    response=CollectorOut,
    auth=AuthBearer(
        [
            ("scada:collector:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def change_collector_status(
    request,
    site_id: int,
    module_id: int,
    collector_id: int,
    payload: CollectorStatusIn,
):
    """修改收集器运行状态"""

    collector = get_object_or_404(
        Collector, id=collector_id, module_id=module_id, module__site_id=site_id
    )
    process_name = get_proccess_name(collector)

    info = rpc.supervisor.getProcessInfo(process_name)
    running = info["statename"] == "RUNNING"
    collector_url = ""

    if payload.running and running:
        # 获取服务地址
        collector_url = get_exporter_url(process_name)

    if not payload.running and running:
        # 停止服务
        result = rpc.supervisor.stopProcessGroup(process_name)
        if result and result[0]["description"] != "OK":
            raise Exception("停止服务错误: " + str(result[0]["description"]))

    if payload.running and not running:
        # 启动服务
        result = rpc.supervisor.startProcessGroup(process_name, True)

        if result and result[0]["description"] != "OK":
            raise Exception("启动服务错误: " + str(result[0]["description"]))

        # 获取服务地址
        for _ in range(0, 3):
            collector_url = get_exporter_url(process_name)

            if not collector_url:
                result = rpc.supervisor.getProcessInfo(process_name)

                if result["statename"] == "RUNNING":
                    time.sleep(1)
                else:
                    break

    out = CollectorOut.from_orm(collector)
    out.running = payload.running
    out.exporter_url = collector_url
    return out


@router.delete(
    "/{site_id}/module/{module_id}/collector/{collector_id}",
    response=str,
    auth=AuthBearer(
        [
            ("scada:collector:delete", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def delete_collector(
    request,
    site_id: int,
    module_id: int,
    collector_id: int,
):
    """删除接口"""

    collector = get_object_or_404(
        Collector, id=collector_id, module_id=module_id, module__site_id=site_id
    )
    collector.delete()

    try:
        delete_process_config(collector)
        supervisor_update()
    except:
        pass

    return "Ok"
