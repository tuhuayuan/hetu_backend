from datetime import datetime
from enum import Enum
from ninja import Schema


class SiteBase(Schema):
    """站点基本结构"""

    # 站点名称
    name: str
    # 联系人姓名
    contact: str
    # 联系人手机号码
    mobile: str
    # 站点状态，可以是整数或其他适当的数据类型
    status: int = 1
    # 备注信息，可以为空
    remark: str | None
    # 默认武汉市的经度
    longitude: float = 114.305215
    # 默认武汉市的纬度
    latitude: float = 30.592849


class SiteIn(SiteBase):
    """创建站点请求结构"""

    pass


class SiteOut(SiteBase):
    """站点返回结构"""

    # ID
    id: int
    # 创建时间
    create_time: datetime


class SiteOptionOut(Schema):
    """选项列表"""

    # ID
    id: int
    # 名称
    name: str


class STATIC_METHOD(str, Enum):
    """统计类型"""

    SUM = "sum"
    AVG = "avg"


class SiteStatisticBase(Schema):
    """统计对象基础结构"""

    # 统计名
    name: str
    # 统计类型
    method: STATIC_METHOD = STATIC_METHOD.SUM
    # 统计对象
    variable_ids: list[int] = []


class SiteStatisticIn(SiteStatisticBase):
    """统计对象创建结构"""

    pass


class SiteStatisticOut(SiteStatisticBase):
    """统计对象选项返回值"""

    # 编号
    id: int


class SiteStatisticValueOut(SiteStatisticOut):
    """统计对象返回结构"""

    # 统计值
    value: float = 0
    # 统计的时间戳
    timestamp: float = 0
