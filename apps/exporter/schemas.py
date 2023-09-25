from ninja import Schema


class ModuleExporter(Schema):
    """数据导出器结构"""

    name: str
    # 模块ID
    module_id: str
    # 模块密钥
    module_secret: str
    # 模块地址
    module_url: str
    # 数据读取间隔（秒）
    interval: int = 5
    # 超时（秒）
    timeout: int = 3
    # 运行状态
    running: bool = False
    # 运行地址
    exporter_url: str = ''


class CreateModuleExporter(Schema):
    """创建请求结构"""

    name: str
    # 模块ID
    module_id: str
    # 模块密钥
    module_secret: str
    # 模块地址
    module_url: str
    # 数据读取间隔（秒）
    interval: int = 5
    # 超时（秒）
    timeout: int = 3


class UpdateModuleExporter(Schema):
    """修改请求结构"""

    name: str
    # 模块密钥
    module_secret: str
    # 模块地址
    module_url: str
    # 数据读取间隔（秒）
    interval: int = 5
    # 超时（秒）
    timeout: int = 3
    # 运行状态
    running: bool = False
