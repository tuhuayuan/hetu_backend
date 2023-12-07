from ninja import Schema


class CollectorOut(Schema):
    """数据导出器结构"""

    id: int
    # 模块ID
    module_id: int
    # 数据读取间隔（秒）
    interval: int = 5
    # 超时（秒）
    timeout: int = 3
    # 运行状态
    running: bool = False
    # 运行地址
    exporter_url: str = ""


class CollectorIn(Schema):
    """创建请求结构"""

    # 数据读取间隔（秒）
    interval: int = 5
    # 超时（秒）
    timeout: int = 3


class CollectorStatusIn(Schema):
    """修改请求结构"""

    # 运行状态
    running: bool = False
