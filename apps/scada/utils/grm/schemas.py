from datetime import datetime

from pydantic import BaseModel


class GrmModuleToken(BaseModel):
    id: str
    # 数据获取的SID
    sid: str
    # 数据地址
    data_url: str

    
class GrmModuleInfo(BaseModel):
    id: str
    # 模块的名称
    name: str
    # 模块的描述
    desc: str
    # 模块的logo
    logo: str
    # 模块登录客户端数量
    logon_clients: int
    # 登录IP
    logon_ip: str
    # 登录时间 
    logon_at: datetime
    # 活跃时间
    last_activate: datetime
    # 状态
    status: int


class GrmVariable(BaseModel):
    # 模块ID
    module_number: str
    # 变量名
    name: str
    # 变量类型 I/F/B
    type: str
    # 变量读写
    rw: bool = False
    # 变量优先等级 0/1/2
    priority: int = 0
    # 变量分组
    group: str = ''
    # 变量描述
    desc: str = ''
    # 变量值
    value: float = 0.0
    # 写入错误
    write_error: int = 0
    # 读取错误
    read_error: int = 0
