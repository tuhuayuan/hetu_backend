from datetime import datetime

from ninja import Schema

from utils.grm.schemas import ModuleInfo
from utils.schema.base import BaseSchemaOut


class GetModuleVar(Schema):
    """列表变量返回格式"""

    # 内部ID
    id: int
    # 模块ID
    module_id: str
    # 变量名
    name: str
    # 变量类型 I/F/B
    type: str
    # 是否本地
    local: bool = False
    # 变量读写
    rw: bool = False
    # 自定义描述
    details: str


class CreateModuleVarIn(Schema):
    """创建变量请求"""

    # 变量名
    name: str
    # 变量类型 I/F/B
    type: str
    # 变量读写
    rw: bool = False
    # 是否本地
    local: bool = False
    # 自定义描述
    details: str


class ReadValueIn(Schema):
    """读取变量请求"""

    # 变量名
    name: str


class ReadValue(Schema):
    """读取变量响应"""

    class Value(Schema):
        # 时间搓
        timestamp: int
        # 值
        value: float

    # 变量名
    name: str
    # 变量类型
    type: str = ""
    # 列表值
    values: list[Value] = []
    # 错误状态
    error: int = 0


class WriteValueIn(Schema):
    """写模块变量请求参数"""

    # 变量名
    name: str
    # 写入值
    value: float


class WriteValueOut(Schema):
    """写模块变量响应参数"""

    # 变量名
    name: str
    # 写入结果
    error: int = 0


class GetModule(Schema):
    """获取模块信息"""

    # 内部ID
    id: int
    # 名称
    name: str
    # 巨控ID
    module_id: str
    # 地址
    module_url: str
    # 最新修改时间
    updated_at: datetime


class GetModuleInfo(GetModule):
    """扩展一下模块信息"""

    # 巨控模块信息
    info: ModuleInfo = None


class CreateModuleIn(Schema):
    """创建模块输入"""

    # 名称
    name: str
    # 巨控ID
    module_id: str
    # 密钥
    module_secret: str
    # 地址
    module_url: str


class UpdateModuleIn(Schema):
    """更新模块信息输入"""

    # 名称可以改
    name: str
    # 密钥
    module_secret: str
    # 地址
    module_url: str
