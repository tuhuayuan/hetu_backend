from django.db import models


class NotifyMessage(models.Model):
    """通知消息模型"""

    # 通知等级
    LEVEL_CHOICES = (
        ('default', '默认'),
        ("info", "信息"),
        ("warning", "警告"),
        ("error", "错误"),
    )

    level = models.CharField(max_length=100, choices=LEVEL_CHOICES)

    # 标题
    title = models.CharField(max_length=255)

    # 内容字段
    content = models.TextField() 

    # 消息来源
    source = models.CharField(max_length=255)

    # 事情发生的时间
    notified_at = models.DateTimeField()

    # 记录消息的时间
    created_at = models.DateTimeField()

    # 是否已确认
    ack = models.BooleanField(default=False)

    # 确认时间，允许为空
    ack_at = models.DateTimeField(null=True)

    # 元数据，使用 JSONField 存储
    meta = models.JSONField()

    def __str__(self):
        return f"{self.title} ({self.level})"
