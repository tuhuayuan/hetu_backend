from datetime import datetime
from ninja import Schema


class RoleIn(Schema):
    """Role请求结构体"""

    # 角色名称
    name: str
    # 角色代码
    code: str
    # 状态 (1: 活动, 0: 非活动)
    status: int
    # 排序
    sort: int


class RoleUpdateIn(Schema):
    """Role更新结构体"""

    # 角色名称
    name: str
    # 状态 (1: 活动, 0: 非活动)
    status: int
    # 排序
    sort: int


class RoleOut(Schema):
    """Role返回结构体"""

    # 编号
    id: int
    # 角色名称
    name: str
    # 角色代码
    code: str
    # 状态 (1: 活动, 0: 非活动)
    status: int
    # 排序
    sort: int
    # 创建时间 (注意：这里使用字符串表示日期时间，因为 auto_created 是 Boolean)
    create_time: datetime
    # 更新时间 (可选)
    update_time: datetime


class DepartmentIn(Schema):
    """定义一个Schema来表示部门模型"""

    # 部门名称
    name: str
    # 部门名称描述
    description: str
    # 部门状态 (1: 活动, 0: 非活动)
    status: int


class DepartmentOut(Schema):
    """定义一个Schema来表示部门模型"""

    # 编号
    id: int
    # 部门名称
    name: str
    # 部门名称描述
    description: str
    # 部门状态 (1: 活动, 0: 非活动)
    status: int
    # 创建时间
    create_time: datetime


class DepartmentUpdateIn(Schema):
    """更新结构"""

    # 部门名称描述
    description: str
    # 部门状态 (1: 活动, 0: 非活动)
    status: int


class UserBase(Schema):
    """用户通用字段"""

    # 昵称
    nickname: str
    # 手机号
    mobile: str
    # 性别标签
    gender_label: str
    # 头像链接
    avatar: str | None
    # 电子邮件
    email: str
    # 状态
    status: int = 1
    # 部门外键 (关联到部门模型)
    dept_id: int
    # 角色外键 (关联到角色模型)
    roles_id: list[int] | None


class UserPasswordIn(Schema):
    """修改密码请求"""

    password: str


class UserUpdateIn(UserBase):
    """用户修改请求结构"""

    # 角色外键 覆盖基类的可选项
    roles_id: list[int]


class UserCreateIn(UserBase):
    """用户创建请求结构体"""

    # 用户名
    username: str
    # 密码
    password: str
    # 角色外键 覆盖基类的可选项
    roles_id: list[int]


class UserOut(UserBase):
    """返回的用户结构体"""

    # 编号
    id: int
    # 用户名
    username: str
    # 创建时间
    create_time: datetime
    # 部门名
    dept_name: str | None
    # 角色名
    roles_name: list[str] | None


class CaptchaOut(Schema):
    """验证码返回结构"""

    # 验证码的加密值
    verify_code_key: str
    # 验证码的图片数据
    verify_code_base64: str


class LoginIn(Schema):
    """登陆请求结构"""

    # 用户名
    username: str
    # 密码
    password: str
    # 验证码
    verify_code: str
    # 验证码加密值
    verify_code_key: str


class LoginOut(Schema):
    """登陆返回结构"""

    # 访问token
    access_token: str
    # token类型
    token_type: str
    # 刷新token
    refresh_token: str | None
    # 过期时间
    expires: datetime | None


class DictTypeBase(Schema):
    """字典类型基本字段"""

    # 字典类型名称
    name: str
    # 字典类型代码
    code: str
    # 字典类型状态
    status: int
    # 备注
    remark: str | None


class DictTypeIn(DictTypeBase):
    """创建字典类型请求"""

    pass


class DictTypeOut(DictTypeBase):
    """返回DictType结构"""

    id: int


class DictDataBase(Schema):
    """Dict数据结构"""

    # 数据标签
    label: str
    # 数据值
    value: str
    # 数据状态 (1: 活动, 0: 非活动)
    status: int
    # 排序值
    sort: int
    # 备注信息
    remark: str | None


class DictDataIn(DictDataBase):
    """请求DictData结构"""

    pass

class DictDataOut(DictDataBase):
    """返回DictData结构"""

    id: int