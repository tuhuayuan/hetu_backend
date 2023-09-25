import fcntl
import os
from typing import Any

import yaml
from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from apps.alert.schemas import AlertRule, AlertRuleIn
from utils.schema.base import api_schema

router = Router()


def prometheus_reload() -> bool:
    """重新加载prometheus配置文件"""

    return False


def build_expr(module_id: str, var_name: str,
               rule_in: AlertRuleIn) -> str:
    """构建规则表达式"""

    alert_exprs = {
        'hight_limit': 'grm_{module_id}_gauge{name="{var_name}"} > {threshold}'
    }

    # 防止出现"符号导致PromQL表达式错误
    var_name = var_name.replace('"', '_')

    return ''


def build_labels(module_id: str, val_name: str,
                 rul_in: AlertRuleIn) -> dict[str, Any]:
    """构建标签"""

    return {}


def build_annotations(module_id: str, val_name: str,
                      rul_in: AlertRuleIn) -> dict[str, Any]:
    """构建注解"""

    return {}


@router.get('/{module_id}', response=list[AlertRule], exclude_unset=True)
@api_schema
def list_alerts(request, module_id: str):
    """列出模块所有设置的Alert，通过Prometheus的rules配置文件实现。
    参考
    https://prometheus.io/docs/prometheus/latest/configuration/recording_rules/
    """

    file_path = f'{settings.PROMETHEUS_RULES_DIR}/grm_{module_id}.rules'

    resp: list[AlertRule] = []
    # 加载配置文件
    if not os.path.exists(file_path):
        return resp

    with open(file_path, 'r') as file:
        try:
            # 获取共享锁
            fcntl.flock(file, fcntl.LOCK_SH)
            data = yaml.safe_load(file)

            # 每个模块变量一个分组
            for g in data['groups']:
                var_name = g['name']

                # 每个alert一条规则
                for r in g['rules']:
                    alert_name = r['alert']
                    annotations = r['annotations']

                    # 构建规则对象
                    ar = AlertRule(
                        moduel_id=module_id,
                        name=alert_name,
                        **annotations)
                    resp.append(ar)

        except Exception as e:
            raise HttpError(500, '读取配置失败: ' + str(e))
        finally:
            # 释放文件锁
            fcntl.flock(file, fcntl.LOCK_UN)

    return resp


@router.post('/{module_id}/{var_name}', response=AlertRule, exclude_unset=True)
@api_schema
def create_alert(request, module_id: str, var_name: str, rule_in: AlertRuleIn):
    """创建规则接口"""

    file_path = f'{settings.PROMETHEUS_RULES_DIR}/grm_{module_id}.rules'

    if not os.path.exists(file_path):
        # 如果不存在则创建文件
        with open(file_path, 'w') as _:
            pass

    # 全程获取文件独占锁
    with open(file_path, 'r+') as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX)
            conf = yaml.safe_load(file)

            # 回到文件起始
            file.seek(0)

            var_group: dict = None
            for g in conf['groups']:
                if g['name'] == var_name:
                    var_group = g
                    break

            if not var_group:
                # 新添加变量规则组
                var_group = {
                    'name': var_name,
                    'rules': []}
                conf['groups'].append(var_group)

            # 如果存在直接覆盖
            for i, r in enumerate(var_group['rules']):
                if r['alert'] == rule_in.name:
                    del var_group['rules'][i]
                    break

            # 构建规则配置
            var_group['rules'].append({
                'alert': rule_in.name,
                'expr': build_expr(module_id, var_name, rule_in),
                'for': rule_in.duration,
                'labels': build_labels(module_id, var_name, rule_in),
                'annotations': build_annotations(module_id, var_name, rule_in)
            })

            # 写入新配置
            yaml.safe_dump(conf, file, allow_unicode=True)
            file.truncate()
        except Exception as e:
            raise HttpError(500, '写入配置失败: ' + str(e))
        finally:
            # 释放文件锁
            fcntl.flock(file, fcntl.LOCK_UN)

    raise HttpError(503, '开发中。。。。')


@router.delete('/{module_id}/{var_name}/{alert_name}', response=str)
@api_schema
def delete_alert(request, module_id: str, var_name: str, 
                 alert_name: str):
    """删除接口"""

    return 'OK'
