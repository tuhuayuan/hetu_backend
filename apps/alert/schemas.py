from datetime import datetime
from enum import Enum

from ninja import Schema


class AlertRule(Schema):
    """警告规则结构"""

    # 所属模块
    module_id: str
    # 变量名
    var_name: str
    # 规则名称
    name: str
    # 描述
    description: str
    # 规则类型
    alert_type: str
    # 警告类型
    alert_level: str = "none"
    # 阈值
    threshold: float = 0.0
    # 状态值
    state: int = 0
    # 权重
    weight: float = 1.0
    # 持续时间
    duration: str = "0s"


class AlertRuleIn(Schema):
    """创建alert请求结构"""

    # 规则名称
    name: str
    # 描述
    description: str
    # 规则类型
    alert_type: str
    # 警告类型
    alert_level: str = "none"
    # 阈值
    threshold: float = 0.0
    # 状态值
    state: int = 0
    # 权重
    weight: float = 1.0
    # 持续时间
    duration: str = "0s"


class NofifyLevel(str, Enum):
    """通知等级"""

    DEFAULT = "default"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotifyMessageOut(Schema):
    """通知消息结构体"""

    #内部ID
    id: int
    # 外部ID
    external_id: str
    # 通知等级
    level: NofifyLevel = NofifyLevel.DEFAULT
    # 标题
    title: str
    # 内容
    content: str
    # 消息来源
    source: str
    # 事情发生时间
    notified_at: datetime
    # 消息创建时间
    created_at: datetime
    # 是否应答
    ack: bool = False
    # 应答时间
    ack_at: datetime = None
    # 元数据
    meta: dict = {}
