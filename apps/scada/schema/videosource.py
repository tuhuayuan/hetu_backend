from ninja import Schema


class SiteVideoSourceBase(Schema):
    """视频监控源"""

    # 设备ID
    device_id: str
    # 设备类别
    device_type: str = "海康"
    # 设备通道
    channel: str = "1"
    # 状态字段
    status: int = 1


class SiteVideoSourceIn(SiteVideoSourceBase):
    """创建视频监控源"""

    pass


class SiteVideoSourceOptionOut(SiteVideoSourceBase):
    """视频监控选项返回（不包含视频链接和截图）"""

    # 内部编号
    id: int
    # 站点id
    site_id: int


class SiteVideoSourceOut(SiteVideoSourceOptionOut):
    """这个包含视频播放地址和截图"""

    # 视频播放地址
    video_source: str = ""
    # 截图地址
    capture: str = ""
    # 访问Token，根据类型不同可能需要
    token: str = ""