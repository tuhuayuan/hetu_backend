from django.db import models


class Module(models.Model):
    """数据模块模型"""

    # 管理端名称
    name = models.CharField(max_length=255, unique=True)
    # 巨控模块账号
    module_number = models.CharField(max_length=255, unique=True)
    # 密钥
    module_secret = models.CharField(max_length=255)
    # 巨控模块地址
    module_url = models.CharField(max_length=255)
    # 修改日期
    updated_at = models.DateTimeField(auto_now=True, auto_created=True)

    def __str__(self) -> str:
        return f"Module: {self.name}"


class Variable(models.Model):
    """数据模块变量模型"""

    # 变量名
    name = models.CharField(max_length=255)
    # 变量类型
    type = models.CharField(max_length=255)
    # 变量读写权限
    rw = models.BooleanField(default=False)
    # 是否本地变量
    local = models.BooleanField(default=False)
    # 变量自定义描述
    details = models.CharField(default="", max_length=255)
    # 所属模块
    module = models.ForeignKey(Module, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return f"Module: {self.module.name}, Var: {self.name}"

    class Meta:
        unique_together = ("name", "module")


class Rule(models.Model):
    """警告规则结构"""

    # 变量
    variable = models.ForeignKey(Variable, on_delete=models.PROTECT)
    # 规则名称
    name = models.CharField(max_length=255)
    # 描述
    description = models.TextField()
    # 规则类型
    alert_type = models.CharField(max_length=255)
    # 警告类型
    alert_level = models.CharField(max_length=255, default="none")
    # 阈值
    threshold = models.FloatField(default=0.0)
    # 状态值
    state = models.IntegerField(default=0)
    # 权重
    weight = models.FloatField(default=1.0)
    # 持续时间
    duration = models.CharField(max_length=20, default="0s")

    class Meta:
        # 定义联合唯一约束
        unique_together = ("name", "variable")

    def __str__(self):
        return self.name


# 通知等级
LEVEL_CHOICES = (
    ("default", "默认"),
    ("info", "信息"),
    ("warning", "警告"),
    ("error", "错误"),
    ("critical", "严重"),
)


class Notify(models.Model):
    """通知消息模型"""

    # 外部的ID标识，表示是否属于同一个事件
    external_id = models.CharField(max_length=255, db_index=True)
    # 通知等级
    level = models.CharField(max_length=255, choices=LEVEL_CHOICES)
    # 标题
    title = models.CharField(max_length=255, db_index=True)
    # 内容字段
    content = models.TextField()
    # 消息来源
    source = models.CharField(max_length=255)
    # 事情发生的时间
    notified_at = models.DateTimeField(db_index=True)
    # 记录消息的时间
    created_at = models.DateTimeField(auto_now_add=True)
    # 是否已确认
    ack = models.BooleanField(default=False)
    # 确认时间，允许为空
    ack_at = models.DateTimeField(null=True)
    # 元数据，使用 JSONField 存储
    meta = models.JSONField(null=True)

    def __str__(self):
        return f"{self.title} ({self.level})"


class Site(models.Model):
    """站点模型"""

    # 站点名称
    name = models.CharField(max_length=255)
    # 联系人姓名
    contact = models.CharField(max_length=255)
    # 联系人手机号码
    mobile = models.CharField(max_length=255)
    # 站点状态，可以是整数或其他适当的数据类型
    status = models.IntegerField(default=1)
    # 记录站点信息创建的日期和时间
    create_time = models.DateTimeField(auto_now_add=True)
    # 备注信息，可以为空
    remark = models.CharField(max_length=255, null=True)


class Graph(models.Model):
    """组态图模型"""

    # 组态名称
    name = models.CharField(max_length=255)
    # 状态字段，用于表示站点配置的状态
    status = models.IntegerField()
    # 记录站点配置信息创建的日期和时间
    create_time = models.DateTimeField(auto_now_add=True)
    # JSON 字段，用于存储绘图相关的配置数据
    data = models.TextField()
    # 备注信息，可以为空
    remark = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Collector(models.Model):
    """采集器模型"""

    # 采集器对应模块
    module = models.OneToOneField(Module, on_delete=models.PROTECT)
    # 采集间隔
    interval = models.IntegerField(default=5)
    # 请求超时
    timeout = models.IntegerField(default=3)
