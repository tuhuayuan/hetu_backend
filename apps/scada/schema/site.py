from datetime import datetime
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