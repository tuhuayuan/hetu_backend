from ninja import Field, Schema


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
    alert_level: str = 'none'
    # 阈值
    threshold: float = 0.0
    # 状态值
    state: int = 0
    # 权重
    weight: float = 1.0
    # 持续时间
    duration: str = '0s'


class AlertRuleIn(Schema):
    """创建alert请求结构"""
    
    # 规则名称
    name: str
    # 描述
    description: str
    # 规则类型
    alert_type: str
    # 警告类型
    alert_level: str = 'none'
    # 阈值
    threshold: float = 0.0
    # 状态值
    state: int = 0
    # 权重
    weight: float = 1.0
    # 持续时间
    duration: str = '0s'