import re
from datetime import datetime
from enum import Enum

from ninja import Schema


class RoleBase(Schema):
    """角色基础结构"""

    # 角色名称
    name: str
    # 角色代码
    code: str
    # 状态 (1: 活动, 0: 非活动)
    status: int
    # 排序
    sort: int

    def validate_code(cls, v):
        pattern = r"^[A-Z][A-Z_]*$"
        if not re.match(pattern, v):
            raise ValueError(
                "Code must start with an uppercase letter and can only contain uppercase letters and underscores."
            )
        return v


class RoleIn(RoleBase):
    """Role请求结构体"""

    pass


class RoleUpdateIn(Schema):
    """Role更新结构体"""

    # 角色名称
    name: str
    # 状态 (1: 活动, 0: 非活动)
    status: int
    # 排序
    sort: int


class RoleOut(RoleBase):
    """Role返回结构体"""

    # 编号
    id: int


class RoleOptionOut(Schema):
    """Role选项列表"""

    # 编号
    id: int
    # 角色名称
    name: str


class RoleMenuIn(Schema):
    """菜单分配权限请求"""

    # 分配的菜单ID
    menus: list[int]


class DepartmentIn(Schema):
    """定义一个Schema来表示部门模型"""

    # 部门名称
    name: str
    # 部门名称描述
    description: str | None
    # 排序
    sort: int = 1
    # 部门状态 (1: 活动, 0: 非活动)
    status: int
    # 上级部门
    parent_id: int | None


class DepartmentOut(Schema):
    """定义一个Schema来表示部门模型"""

    # 编号
    id: int
    # 部门名称
    name: str
    # 部门名称描述
    description: str | None
    # 排序
    sort: int = 1
    # 部门状态 (1: 活动, 0: 非活动)
    status: int
    # 创建时间
    create_time: datetime
    # 上级部门ID
    parent_id: int | None


class DepartmentListOut(DepartmentOut):
    """部门列表树结构"""

    children: list["DepartmentListOut"] = []


class DepartmentOptionOut(Schema):
    """部门选项树结构"""

    # 编号
    id: int
    # 部门名称
    name: str
    # 子部门
    children: list["DepartmentOptionOut"] = None


class DepartmentUpdateIn(Schema):
    """更新结构"""

    # 部门名称描述
    description: str | None
    # 排序
    sort: int = 1
    # 部门状态 (1: 活动, 0: 非活动)
    status: int
    # 上级部门ID
    parent_id: int | None


class UserBase(Schema):
    """用户通用字段"""

    # 昵称
    nickname: str
    # 手机号
    mobile: str | None
    # 性别标签
    gender_label: str | None
    # 头像链接
    avatar: str | None
    # 电子邮件
    email: str | None
    # 状态
    status: int = 1


class UserUpdateIn(UserBase):
    """用户修改请求结构"""

    # 部门外键 (关联到部门模型)
    dept_id: int
    # 角色外键 (关联到角色模型)
    role_ids: list[int]


class UserCreateIn(UserBase):
    """用户创建请求结构体"""

    # 用户名
    username: str
    # 密码
    password: str = "password"
    # 部门外键 (关联到部门模型)
    dept_id: int
    # 角色外键 (关联到角色模型)
    role_ids: list[int]

    def validate_username(cls, v):
        pattern = r"^[a-z][a-z0-9_]*$"
        if not re.match(pattern, v):
            raise ValueError(
                "Username must start with a lowercase letter and can only contain lowercase letters, numbers, and underscores."
            )
        return v


class UserPasswordIn(Schema):
    """修改密码请求"""

    password: str


class UserCreateOut(UserBase):
    """用户创建响应结构体"""

    # 编号
    id: int
    # 用户名
    username: str
    # 部门外键 (关联到部门模型)
    dept_id: int
    # 角色外键 (关联到角色模型)
    role_ids: list[int]


class UserListOut(UserBase):
    """返回的用户结构体"""

    # 编号
    id: int
    # 用户名
    username: str
    # 创建时间
    create_time: datetime
    # 部门名
    dept_name: str
    # 角色名
    role_names: list[str]


class UserLoginInfoOut(Schema):
    """用户详细信息结构体"""

    # 编号
    id: int
    # 用户名
    nickname: str
    # 头像链接
    avatar: str | None
    # 角色名
    role_names: list[str] = []
    # 用户权限列表
    perms: list[str] = []


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
    """登录返回结构"""

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

    # 类型编码
    type_code: str
    # 数据标签
    name: str
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


class DictDataOptionOut(Schema):
    """DictData选项列表"""

    # key
    name: str
    # value
    value: str


class MenuType(str, Enum):
    """菜单类型"""

    CATALOG = "CATALOG"
    MENU = "MENU"
    BUTTON = "BUTTON"
    EXTLINK = "EXTLINK"


class MenuBase(Schema):
    """菜单请求基本结构"""

    # 上级菜单
    parent_id: int | None
    # 菜单项名称
    name: str
    # 菜单项类型（可选项：CATALOG、MENU、BUTTON、EXTLINK）
    menu_type: MenuType
    # 菜单项路径 (可选，可以为 None)
    path: str | None
    # 菜单项对应的组件名称 (可选，可以为 None)
    component: str | None
    # 菜单项排序值，默认为 1
    sort: int = 1
    # 菜单项是否可见，默认为 True
    visible: bool = True
    # 菜单项图标
    icon: str | None
    # 菜单项重定向路径 (可选，可以为 None)
    redirect: str | None
    # 菜单项权限（可选，用于权限控制，可以为 None）
    perm: str | None


class MenuIn(MenuBase):
    """菜单创建请求结构"""

    pass


class MenuInfoOut(MenuBase):
    """菜单创建返回结构体"""

    id: int


class MenuTreeOut(MenuBase):
    """菜单树列表结构"""

    id: int
    children: list["MenuInfoOut"] = []


class MenuTreeOptionOut(Schema):
    """菜单名树形列表"""

    id: int
    name: str
    children: list["MenuTreeOptionOut"] = None


class MenuTreeRouterOut(Schema):
    """菜单路由树列表"""

    class RouterMeta(Schema):
        """meta数据结构"""

        # 路由标题
        title: str
        # 路由图标
        icon: str | None
        # 是否隐藏路由
        hidden: bool
        # 路由角色列表
        roles: list[str]
        # 是否保持路由活动状态，默认为 True
        keep_alive: bool = True

    # 路由路径
    path: str | None
    # 路由组件
    component: str | None
    # 路由名称 (可选，可以为 None)
    name: str | None
    # 路由重定向路径 (可选，可以为 None)
    redirect: str | None
    # 路由的 meta 数据
    meta: RouterMeta | None
    # 子路由列表
    children: list["MenuTreeRouterOut"] = None

