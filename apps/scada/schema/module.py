from datetime import datetime

from ninja import Schema

from apps.scada.utils.grm.schemas import GrmModuleInfo



class ModuleIn(Schema):
    """创建模块输入"""

    # 站点ID
    site_id: int
    # 名称
    name: str
    # 巨控ID
    module_number: str
    # 密钥
    module_secret: str
    # 地址
    module_url: str


class ModuleUpdateIn(Schema):
    """修改模块输入结构"""

    # 名称
    name: str
    # 密钥
    module_secret: str
    # 地址
    module_url: str


class ModuleOut(Schema):
    """模块信息结构"""

    # 内部ID
    id: int
    # 名称
    name: str
    # 模块编号
    module_number: str
    # 地址
    module_url: str
    # 最新修改时间
    updated_at: datetime
    # 站点id
    site_id: int


class ModuleOptionOut(Schema):
    """模块选项结构"""

    # 内部ID
    id: int
    # 名称
    name: str
    # 模块编号
    module_number: str
    # 站点id
    site_id: int


class ModuleInfoOut(ModuleOut):
    """扩展一下模块信息"""

    # 巨控模块信息
    info: GrmModuleInfo = None
