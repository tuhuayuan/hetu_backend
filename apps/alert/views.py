import fcntl
import hashlib
import json
import os
from datetime import datetime
from typing import Any
from django.shortcuts import get_object_or_404

import requests
import yaml
from dateutil.parser import parser
from django.conf import settings
from django.http import HttpRequest
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from apps.alert.models import NotifyMessage
from apps.alert.schemas import AlertRule, AlertRuleIn, NotifyMessageOut
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()

rfc3339_parser = parser()


def build_expr(module_id: str, var_name: str, rule_in: AlertRuleIn) -> str:
    """构建规则表达式"""

    # 防止出现"符号导致PromQL表达式错误
    var_name = var_name.replace('"', "_")

    metric_selector = 'grm_{module_id}_gauge{{name="{var_name}"}}'.format(
        module_id=module_id, var_name=var_name
    )

    alert_exprs = {
        "hight_limit": "{metric_selector} > {threshold}",
        "low_limit": "{metric_selector} < {threshold}",
        "binary_state": "{metric_selector} == {state}",
        "no_change": "changes({metric_selector}[{duration}]) == 0",
    }

    if rule_in.alert_type in alert_exprs:
        return alert_exprs[rule_in.alert_type].format(
            metric_selector=metric_selector, **rule_in.dict()
        )
    else:
        raise Exception(f"alert type {rule_in.alert_type} not implemented.")


def build_labels(module_id: str, var_name: str, rule_in: AlertRuleIn) -> dict[str, Any]:
    """构建标签"""

    return {
        "severity": rule_in.alert_level,
        "module_id": module_id,
        "var_name": var_name,
    }


def build_annotations(
    module_id: str, var_name: str, rul_in: AlertRuleIn
) -> dict[str, Any]:
    """构建注解"""

    return {
        "module_id": module_id,
        "var_name": var_name,
        **rul_in.dict(exclude={"name"}, exclude_unset=True),
    }


def reload_config():
    """重新加载rules配置文件"""

    resp = requests.post(settings.PROMETHEUS_URL + "/-/reload")
    resp.raise_for_status()


@router.get("/rules/{module_id}", response=list[AlertRule], exclude_unset=True)
@api_paginate
def list_alerts(request, module_id: str):
    """列出模块所有设置的Alert，通过Prometheus的rules配置文件实现。
    参考
    https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/
    """

    file_path = f"{settings.PROMETHEUS_RULES_DIR}/grm_{module_id}.rules"

    resp: list[AlertRule] = []
    # 加载配置文件
    if not os.path.exists(file_path):
        return resp

    with open(file_path, "r") as file:
        try:
            # 获取共享锁
            fcntl.flock(file, fcntl.LOCK_SH)
            data = yaml.safe_load(file)

            # 每个模块变量一个分组
            for g in data["groups"]:
                var_name = g["name"]

                # 每个alert一条规则
                for r in g["rules"]:
                    alert_name = r["alert"]
                    annotations = r["annotations"]

                    # 构建规则对象
                    ar = AlertRule(moduel_id=module_id, name=alert_name, **annotations)
                    resp.append(ar)

        except Exception as e:
            raise HttpError(500, "读取配置失败: " + str(e))
        finally:
            # 释放文件锁
            fcntl.flock(file, fcntl.LOCK_UN)

    return resp


@router.post("/rules/{module_id}/{var_name}", response=AlertRule, exclude_unset=True)
@api_schema
def create_alert(request, module_id: str, var_name: str, rule_in: AlertRuleIn):
    """创建规则接口"""

    file_path = f"{settings.PROMETHEUS_RULES_DIR}/grm_{module_id}.rules"

    if not os.path.exists(file_path):
        # 如果不存在则创建文件
        with open(file_path, "w") as _:
            pass

    # 全程获取文件独占锁
    with open(file_path, "r+") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX)
            conf = yaml.safe_load(file)

            # 回到文件起始
            file.seek(0)

            # 获取变量组
            var_group: dict = None
            for g in conf["groups"]:
                if g["name"] == var_name:
                    var_group = g
                    break

            if not var_group:
                # 新添加变量规则组
                var_group = {"name": var_name, "rules": []}
                conf["groups"].append(var_group)

            # 如果存在直接覆盖
            for i, r in enumerate(var_group["rules"]):
                if r["alert"] == rule_in.name:
                    del var_group["rules"][i]
                    break

            # 构建规则配置
            var_group["rules"].append(
                {
                    "alert": rule_in.name,
                    "expr": build_expr(module_id, var_name, rule_in),
                    "for": rule_in.duration,
                    "labels": build_labels(module_id, var_name, rule_in),
                    "annotations": build_annotations(module_id, var_name, rule_in),
                }
            )

            # 写入新配置
            yaml.safe_dump(conf, file, allow_unicode=True)
            file.truncate()

            # 热加载
            reload_config()

            return AlertRule(
                module_id=module_id,
                var_name=var_name,
                **rule_in.dict(exclude_unset=True),
            )

        except Exception as e:
            raise HttpError(500, "写入配置失败: " + str(e))
        finally:
            # 释放文件锁
            fcntl.flock(file, fcntl.LOCK_UN)


@router.delete("/rules/{module_id}/{var_name}/{alert_name}", response=str)
@api_schema
def delete_alert(request, module_id: str, var_name: str, alert_name: str):
    """删除接口"""
    file_path = f"{settings.PROMETHEUS_RULES_DIR}/grm_{module_id}.rules"

    if os.path.exists(file_path):
        # 全程获取文件独占锁
        with open(file_path, "r+") as file:
            try:
                fcntl.flock(file, fcntl.LOCK_EX)
                conf = yaml.safe_load(file)

                # 回到文件起始
                file.seek(0)

                var_group: dict = None
                for g in conf["groups"]:
                    if g["name"] == var_name:
                        var_group = g
                        break

                # 定位并且删除alert
                for i, r in enumerate(var_group["rules"]):
                    if r["alert"] == alert_name:
                        del var_group["rules"][i]

                        # 写配置
                        yaml.safe_dump(conf, file, allow_unicode=True)
                        file.truncate()

                        # 热加载
                        reload_config()

                        return "OK"

            except Exception as e:
                raise HttpError(500, "删除配置文件: " + str(e))
            finally:
                # 释放文件锁
                fcntl.flock(file, fcntl.LOCK_UN)

    raise HttpError(404, "配置不存在")


@router.post("/notify", response=str)
@api_schema
def create_notify(request: HttpRequest):
    """接收alertmanger的webhook通知调用, 并转换成系统的通知信息
    调用的JSON格式参考
    https://prometheus.io/docs/alerting/latest/configuration/#webhook_config
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        alerts = data["alerts"]
    except json.JSONDecodeError as e:
        raise HttpError(403, str(e))

    for alert in alerts:
        status = alert["status"]
        annos = alert["annotations"]
        labels = alert["labels"]

        # 计算外部ID
        hasher = hashlib.sha1(
            (labels["module_id"] + labels["var_name"] + labels["alertname"]).encode()
        )
        external_id = hasher.hexdigest()

        # 统一单挑通知的创建时间
        created_at = datetime.now(timezone.utc)

        # 最后一条
        last_one = (
            NotifyMessage.objects.filter(external_id=external_id)
            .order_by("-notified_at")
            .first()
        )

        # 通知时间发生的时间
        if status == "firing":
            notified_at = rfc3339_parser.parse(timestr=alert["startsAt"])

            # 标题后缀
            suffix_title = "触发警告"
            # 警告等级按照来源设置
            level = labels["severity"]
        else:
            notified_at = rfc3339_parser.parse(timestr=alert["endsAt"])

            # 标题后缀
            suffix_title = "解除警告"
            # 强制等级为info级别
            level = "info"

        # 收到的是早期的消息则不管
        if last_one and notified_at <= last_one.notified_at:
            continue

        # 构造title
        title = (
            labels["module_id"]
            + "::"
            + labels["var_name"]
            + "::"
            + labels["alertname"]
            + "::"
            + suffix_title
        )

        # 构建模型实力
        message = NotifyMessage(
            external_id=external_id,
            level=level,
            title=title,
            content=annos["description"],
            source="alertmanager",
            notified_at=notified_at,
            created_at=created_at,
            meta=annos,
        )
        message.save()

    return "OK"


@router.get("/notify", response=list[NotifyMessageOut])
@api_paginate
def list_notify(request, module_id: str, var_name: str = None, ack: bool = None):
    """列出模块通知"""

    f_title = module_id + "::"
    if var_name:
        f_title = f_title + var_name + "::"

    f_kwargs = {"title__startswith": f_title}

    if ack:
        f_kwargs["ack"] = ack

    results = NotifyMessage.objects.filter(**f_kwargs).order_by("-notified_at")

    return results


@router.post("/notify/{notify_id}", response=str)
@api_schema
def ack_notify(request, notify_id: int):
    """标记已读"""

    try:
        message = get_object_or_404(NotifyMessage, id=notify_id)
    except:
        raise HttpError(404, '通知对象不存在')

    if not message.ack:
        message.ack = True
        message.ack_at = datetime.now(timezone.utc)
        message.save()

    return "OK"
