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
    sort = models.IntegerField()
    # 创建时间
    create_time = models.DateTimeField(auto_created=True)
    # 更新时间 (可选)
    update_time = models.DateTimeField(auto_now=True)


class RoleMenuId(models.Model):
    """角色菜单"""

    # 菜单ID
    menu_id = models.IntegerField()

    # 角色
    role = models.ForeignKey(Role, on_delete=models.CASCADE)


class Department(models.Model):
    """部门模型"""

    # 部门名称
    name = models.CharField(max_length=255)
    # 部门名称描述
    description = models.CharField(max_length=255)
    # 创建时间
    create_time = models.DateTimeField()
    # 部门状态
    status = models.IntegerField()

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
    mobile = models.CharField(max_length=20)
    # 性别标签
    gender_label = models.CharField(max_length=10)
    # 头像链接
    avatar = models.URLField(max_length=255, null=True)
    # 电子邮件
    email = models.EmailField(null=True)
    # 用户状态
    status = models.IntegerField(default=1)
    # 部门外键
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    # 角色外键
    roles = models.ManyToManyField(Role)
    # 创建时间
    create_time = models.DateTimeField()

    def __str__(self):
        return self.username


class DictType(models.Model):
    """字典类型模型"""

    # 字典类型名称
    name = models.CharField(max_length=255)
    # 字典类型代码
    code = models.CharField(max_length=255)
    # 字典类型状态
    status = models.IntegerField()


class DictData(models.Model):
    """字典数据模型"""

    # 字典数据名称
    label = models.CharField(max_length=255)
    # 字典数据值
    value = models.CharField(max_length=255)
    # 字典数据状态
    status = models.IntegerField()
    # 外键，关联到字典类型
    dict_type = models.ForeignKey(DictType, on_delete=models.CASCADE)


class Route(models.Model):
    """菜单路由模型"""

    # 路由名称
    name = models.CharField(max_length=255)
    # 路由路径
    path = models.CharField(max_length=255)
    # 路由组件
    component = models.CharField(max_length=255)
    # 菜单标题
    title = models.CharField(max_length=100)
    # 菜单图标
    icon = models.CharField(max_length=100)
    # 是否隐藏菜单
    hidden = models.BooleanField(default=False)
    # 是否保持活跃状态
    keep_alive = models.BooleanField(default=True)
    # 角色外键
    role = models.ManyToManyField(Role)
