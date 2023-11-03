from datetime import datetime

from ninja import Schema


class GraphBase(Schema):
    # 组态名称
    name: str
    # 状态字段，用于表示站点配置的状态
    status: int = 1
    # JSON 字段，用于存储绘图相关的配置数据
    data: str = ""
    # 备注信息，可以为空
    remark: str | None
    # 排序
    order: int = 0
    # 站点ID
    site_id: int


class GraphIn(GraphBase):
    """组态图创建结构"""

    pass


class GraphOut(GraphBase):
    """组态图输出结构"""

    # ID
    id: int
    # 创建时间
    create_time: datetime


class GraphOptionOut(Schema):
    """组态图选项输出结构"""

    # ID
    id: int
    # 组态名称
    name: str
