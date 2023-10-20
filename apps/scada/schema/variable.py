from ninja import Schema


class VariableBase(Schema):
    """变量基础结构"""

    # 变量模块
    module_id: int
    # 变量名
    name: str
    # 变量组
    group: str
    # 变量类型 I/F/B
    type: str
    # 变量读写
    rw: bool = False
    # 是否本地
    local: bool = False
    # 自定义描述
    details: str


class VariableOut(VariableBase):
    """变量返回结构"""

    # 内部ID
    id: int


class VariableGroupOut(Schema):
    """变量组返回结构"""

    group: str


class VariableOptionOut(Schema):
    """选项列表结构"""

    # 内部ID
    id: int
    # 变量名
    name: str
    # 变量组
    group: str
    # 变量类型 I/F/B
    type: str
    # 变量读写
    rw: bool = False


class VariableIn(VariableBase):
    """创建变量请求结构"""

    pass


class VariableUpdateIn(Schema):
    """更新请求结构"""

    # 变量类型 I/F/B
    type: str
    # 变量读写
    rw: bool = False
    # 自定义描述
    details: str


class ReadValueOut(Schema):
    """变量值结构体"""

    class Value(Schema):
        # 时间搓
        timestamp: int
        # 值
        value: float

    # 变量ID
    id: int
    # 模块ID
    module_id: int
    # 变量名
    name: str
    # 变量类型
    type: str = ""
    # 变量读写
    rw: bool = False
    # 列表值
    values: list[Value] = []
    # 错误状态
    error: int = 0


class WriteValueIn(Schema):
    """写模块变量请求参数"""

    # 变量ID
    id: int
    # 写入值
    value: float


class WriteValueOut(Schema):
    """写模块变量响应参数"""

    # 变量ID
    id: int
    # 写入结果
    error: int = 0
