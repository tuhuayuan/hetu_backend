from django.shortcuts import get_object_or_404
from ninja import Router
from apps.scada.models import SiteVideoSource

from apps.scada.schema.videosource import SiteVideoSourceIn, SiteVideoSourceOptionOut, SiteVideoSourceOut
from apps.scada.utils.ys import get_accecc_token, get_capture_url, get_video_url
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema


router = Router()


@router.post(
    "/{site_id}/videosource",
    response=SiteVideoSourceOptionOut,
    auth=AuthBearer(
        [
            ("scada:site:create", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def create_videosource(request, site_id: int, payload: SiteVideoSourceIn):
    """给站点添加视频源"""

    svs = SiteVideoSource(site_id=site_id, **payload.dict())
    svs.save()
    return svs


@router.get(
    "/{site_id}/videosource",
    response=list[SiteVideoSourceOptionOut],
    auth=AuthBearer(
        [
            ("scada:site:get", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def list_videosource(request, site_id: int):
    """列出视频源"""

    return SiteVideoSource.objects.filter(site_id=site_id).all()


@router.get(
    "/{site_id}/videosource/{videosource_id}",
    response=SiteVideoSourceOut,
    auth=AuthBearer(
        [
            ("scada:site:get", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_videosource(request, videosource_id: int, site_id: int):
    """调用视频源接口获取播放地址和截图"""

    video = get_object_or_404(SiteVideoSource, id=videosource_id, site_id=site_id)
    output = SiteVideoSourceOut.from_orm(video)

    try:
        output.capture = get_capture_url(
            device_serial=video.device_id, channel_no=int(video.channel)
        )
        output.video_source = get_video_url(
            device_serial=video.device_id, channel_no=int(video.channel)
        )
        output.token = get_accecc_token()
    except Exception as e:
        # raise HttpError(500, f"获取视频截图或播放地址错误: {e}")
        pass

    return output


@router.delete(
    "/{site_id}/videosource/{videosource_id}",
    response=str,
    auth=AuthBearer(
        [
            ("scada:site:create", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def delete_videosource(request, site_id: int, videosource_id: int):
    """删除通道"""

    svs = get_object_or_404(SiteVideoSource, id=videosource_id, site_id=site_id)
    svs.delete()
    return "Ok"
