from django.db import models


class Role(models.Model):
    """角色模型"""

    # 角色名称
    name = models.CharField(max_length=255)
    # 角色代码
    code = models.CharField(max_length=50, unique=True)
    # 状态 (1: 活动, 0: 非活动)
    status = models.IntegerField(default=1)
    # 排序
    sort = models.IntegerField(default=1)
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True)
    # 更新时间 (可选)
    update_time = models.DateTimeField(auto_now=True)


class Department(models.Model):
    """部门模型"""

    # 部门名称
    name = models.CharField(max_length=255)
    # 部门名称描述
    description = models.CharField(max_length=255)
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True)
    # 排序
    sort = models.IntegerField(default=1)
    # 部门状态
    status = models.IntegerField(default=1)
    # 上级部门
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class User(models.Model):
    """用户模型"""

    # 用户名
    username = models.CharField(max_length=255, unique=True)
    # 密码
    password = models.CharField(max_length=100)
    # 昵称
    nickname = models.CharField(max_length=255)
    # 手机号
    mobile = models.CharField(max_length=20, null=True)
    # 性别标签
    gender_label = models.CharField(max_length=10, null=True)
    # 头像链接
    avatar = models.URLField(max_length=255, null=True)
    # 电子邮件
    email = models.EmailField(null=True)
    # 用户状态
    status = models.IntegerField(default=1)
    # 部门外键
    dept = models.ForeignKey(Department, on_delete=models.PROTECT)
    # 角色外键
    roles = models.ManyToManyField(Role)
    # 创建时间
    create_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class DictType(models.Model):
    """字典类型模型"""

    # 字典类型名称
    name = models.CharField(max_length=255)
    # 字典类型代码
    code = models.CharField(max_length=255, unique=True)
    # 字典类型状态
    status = models.IntegerField(default=1)
    # 备注
    remark = models.CharField(max_length=255, null=True)


class DictData(models.Model):
    """字典数据模型"""

    # 字典数据名
    name = models.CharField(max_length=255)
    # 字典数据值
    value = models.CharField(max_length=255)
    # 字典数据状态
    status = models.IntegerField(default=1)
    # 排序
    sort = models.IntegerField(default=1)
    # 描述
    remark = models.CharField(max_length=255, null=True)
    # 字典类型码
    type_code = models.CharField(max_length=255)


class Menu(models.Model):
    """系统菜单模型"""

    # 上级菜单（自关联外键，如果没有上级菜单，则为顶级菜单）
    parent = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    # 菜单项名称
    name = models.CharField(max_length=255)
    # 菜单项类型（可选项：CATALOG、MENU、BUTTON、EXTLINK）
    menu_type = models.CharField(
        max_length=255,
        choices=[
            ("CATALOG", "目录"),
            ("MENU", "菜单"),
            ("BUTTON", "按钮"),
            ("EXTLINK", "外部链接"),
        ],
    )
    # 菜单项路径
    path = models.CharField(max_length=255, null=True)
    # 菜单项对应的组件名称
    component = models.CharField(max_length=255, null=True)
    # 菜单项排序值
    sort = models.IntegerField(default=1)
    # 菜单项是否可见（1 表示可见，0 表示不可见）
    visible = models.IntegerField(default=1)
    # 菜单项图标
    icon = models.CharField(max_length=255, null=True)
    # 菜单项重定向路径
    redirect = models.CharField(max_length=255, null=True)
    # 菜单项权限（可选，用于权限控制）
    perm = models.CharField(max_length=255, null=True, unique=True)
    # 角色
    roles = models.ManyToManyField(Role)

    def __str__(self):
        return self.name
