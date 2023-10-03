import configparser
import fcntl
import glob
import os
import time
from string import Template
from xmlrpc.client import ServerProxy

from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from apps.exporter.schemas import (CreateModuleExporter, ModuleExporter,
                                   UpdateModuleExporter)
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()

rpc = ServerProxy(settings.SUPERVISOR_XMLRPC_URL)


supervisor_tpl = Template(
    """
[program:$process_name]
command=$command
environment=MODULE_ID="$module_id",MODULE_SECRET="$module_secret",MODULE_URL="$module_url",RANDOM_PORT=$port,HOST="$host",ADVERTISE="$advertise"
autostart=false

[module]
name=$name
module_id=$module_id
module_secret=$module_secret
module_url=$module_url
export_interval=$interval
export_timeout=$timeout
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


@router.get("/", response=list[ModuleExporter])
@api_paginate
def list_exporter(request):
    file_list = glob.glob(settings.SUPERVISOR_EXPORT_DIR + "/exporter_*.conf")
    exporter_list: list[ModuleExporter] = []

    for path in file_list:
        # 获取配置文件
        config = configparser.ConfigParser()
        config.read(path)
        process_name = config.sections()[0].split(":")[1]

        exporter = ModuleExporter(
            name=config.get("module", "name"),
            module_id=config.get("module", "module_id"),
            module_secret=config.get("module", "module_secret"),
            module_url=config.get("module", "module_url"),
            interval=config.get("module", "export_interval"),
            timeout=config.get("module", "export_timeout"),
        )

        # 获取运行状态
        info = rpc.supervisor.getProcessInfo(process_name)
        exporter.running = info["statename"] == "RUNNING"

        # 获取运行地址
        if exporter.running:
            exporter.exporter_url = get_exporter_url(process_name)

        # 压入列表
        exporter_list.append(exporter)

    return exporter_list


@router.post("/", response=ModuleExporter)
@api_schema
def create_exporter(request, data: CreateModuleExporter):
    """创建数据收集器"""

    process_name = f"exporter_{data.module_id}"
    file_path = f"{settings.SUPERVISOR_EXPORT_DIR}/{process_name}.conf"

    # 配置文件内容
    content = supervisor_tpl.substitute(
        name=data.name,
        process_name=process_name,
        module_id=data.module_id,
        module_secret=data.module_secret,
        module_url=data.module_url,
        interval=data.interval,
        timeout=data.timeout,
        command=settings.SUPERVISOR_EXPORT_COMMAND,
        host=settings.SUPERVISOR_EXPORT_HOST,
        port=settings.SUPERVISOR_EXPORT_PORT,
        advertise=settings.SUPERVISOR_EXPORT_ADVERTISE,
    )
    # 创建配置文件
    if not os.path.exists(file_path):
        # 获得文件锁
        with open(file_path, "w") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # 在这里进行其他进程不能创建文件的操作
                file.write(content)
            finally:
                # 释放文件锁
                fcntl.flock(file, fcntl.LOCK_UN)
    else:
        raise HttpError(409, "已经存在")

    # Update
    try:
        supervisor_update()
    except:
        raise HttpError(503, "配置没有生效")

    # 创建返回对象
    resp = ModuleExporter(**data.dict())

    return resp


@router.post("/{module_id}", response=ModuleExporter)
@api_schema
def update_exporter(request, module_id: str, data: UpdateModuleExporter):
    """更新接口，包含启动和停止"""

    process_name = f"exporter_{module_id}"
    file_path = f"{settings.SUPERVISOR_EXPORT_DIR}/exporter_{module_id}.conf"

    # 加载配置文件
    if os.path.exists(file_path):
        # 修改配置
        with open(file_path, "w") as file:
            try:
                # 获得文件锁
                fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)

                # 配置文件内容
                content = supervisor_tpl.substitute(
                    name=data.name,
                    process_name=process_name,
                    module_id=module_id,
                    module_secret=data.module_secret,
                    module_url=data.module_url,
                    interval=data.interval,
                    timeout=data.timeout,
                    command=settings.SUPERVISOR_EXPORT_COMMAND,
                    host=settings.SUPERVISOR_EXPORT_HOST,
                    port=settings.SUPERVISOR_EXPORT_PORT,
                    advertise=settings.SUPERVISOR_EXPORT_ADVERTISE,
                )
                file.write(content)
            except Exception as e:
                raise HttpError(500, "更新配置失败: " + str(e))
            finally:
                # 释放文件锁
                fcntl.flock(file, fcntl.LOCK_UN)

        # 应用配置文件
        try:
            supervisor_update()
        except:
            raise HttpError(500, "配置没有生效")

        # 更新运行状态
        try:
            info = rpc.supervisor.getProcessInfo(process_name)
            running = info["statename"] == "RUNNING"
            exporter_url = ""

            if data.running and running:
                # 获取服务地址
                exporter_url = get_exporter_url(process_name)

            if data.running and not running:
                # 删除日志
                os.remove(info["stdout_logfile"])

                # 启动服务
                result = rpc.supervisor.startProcessGroup(process_name, True)

                if result and result[0]["description"] != "OK":
                    raise Exception("启动服务错误: " + str(result[0]["description"]))

                # 获取服务地址
                for _ in range(0, 3):
                    exporter_url = get_exporter_url(process_name)

                    if not exporter_url:
                        result = rpc.supervisor.getProcessInfo(process_name)

                        if result["statename"] == "RUNNING":
                            time.sleep(1)
                        else:
                            break

            if not data.running and running:
                # 停止服务
                result = rpc.supervisor.stopProcessGroup(process_name)
                if result and result[0]["description"] != "OK":
                    raise Exception("停止服务错误: " + str(result[0]["description"]))

        except:
            raise HttpError(500, "更新运行状态失败")
    else:
        raise HttpError(404, "配置不存在")

    resp = ModuleExporter(module_id=module_id, exporter_url=exporter_url, **data.dict())
    return resp


@router.delete("/{module_id}", response=str)
@api_schema
def delete_exporter(request, module_id):
    """删除接口"""
    file_path = f"{settings.SUPERVISOR_EXPORT_DIR}/exporter_{module_id}.conf"

    # 加载配置文件
    if os.path.exists(file_path):
        # 删除配置文件
        try:
            os.remove(file_path)
        except OSError as e:
            raise HttpError(500, f"删除配置文件失败：{e}")

        # Update
        try:
            supervisor_update()
        except:
            raise HttpError(500, "更新配置")

    else:
        raise HttpError(404, "配置不存在")

    return "OK"


@router.get("/metrics/running")
def service_discover(request):
    """实现Prometheus的HTTP SD接口
    https://prometheus.io/docs/prometheus/latest/http_sd/
    """
    file_list = glob.glob(settings.SUPERVISOR_EXPORT_DIR + "/exporter_*.conf")
    resp = []

    for path in file_list:
        # 获取配置文件
        config = configparser.ConfigParser()
        config.read(path)

        # 进程名
        process_name = config.sections()[0].split(":")[1]

        # 获取进程状态
        try:
            info = rpc.supervisor.getProcessInfo(process_name)

            if info["statename"] == "RUNNING":
                # 加入服务发现
                resp.append(
                    {
                        "targets": [get_exporter_url(process_name)],
                        "labels": {
                            "__meta_inverval": "5s",
                        },
                    }
                )
        except:
            # 不需要处理错误
            continue

    return 200, resp
