from django.db import models


class GrmModule(models.Model):
    """GRM巨控数据模块模型"""

    # 管理端名称
    name = models.CharField(max_length=200, unique=True)
    # 巨控模块ID
    module_id = models.CharField(max_length=50, unique=True)
    # 密钥
    module_secret = models.CharField(max_length=50)
    # 巨控模块地址
    module_url = models.CharField(max_length=255)
    # 修改日期
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Module: {self.name}"


class GrmModuleVar(models.Model):
    """GRM巨控模块变量"""

    # 变量名
    name = models.CharField(max_length=200)
    # 变量类型
    type = models.CharField(max_length=50)
    # 变量读写权限
    rw = models.BooleanField(default=False)
    # 是否本地变量
    local = models.BooleanField(default=False)
    # 变量自定义描述
    details = models.CharField(default="", max_length=200)

    # 所属模块
    module = models.ForeignKey(
        GrmModule,
        to_field="module_id",
        db_column="module_id",
        related_name="vars",
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return f"Module: {self.module.name}, Var: {self.name}"

    class Meta:
        unique_together = ("name", "module")
