from urllib.parse import urlencode
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from ninja import Router
import requests

from apps.scada.models import Site, SiteStatistic, SiteVideoSource
from apps.scada.schema.site import (
    SiteIn,
    SiteOptionOut,
    SiteOut,
    SiteStatisticIn,
    SiteStatisticOut,
    SiteStatisticValueOut,
    SiteVideoSourceIn,
    SiteVideoSourceOptionOut,
    SiteVideoSourceOut,
)
from apps.scada.utils.ys import get_capture_url, get_video_url, get_accecc_token
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post(
    "",
    response=SiteOut,
    auth=AuthBearer([("scada:site:create", "x")]),
)
@api_schema
def create_site(request, payload: SiteIn):
    """创建站点"""

    site = Site(**payload.dict())
    site.save()
    return site


@router.get(
    "options",
    response=list[SiteOptionOut],
    auth=AuthBearer([("scada:site:list", "x")]),
)
@api_schema
def get_site_option_list(request):
    """选项列表"""

    return Site.objects.all()


@router.get(
    "",
    response=list[SiteOut],
    auth=AuthBearer([("scada:site:list", "x")]),
)
@api_paginate
def get_site_list(request, keywords: str = None):
    """获取信息列表"""

    sites = Site.objects.all()

    if keywords:
        sites = sites.filter(
            Q(name__icontains=keywords) | Q(contact__icontains=keywords)
        )

    return sites


@router.get(
    "/{site_id}",
    response=SiteOut,
    auth=AuthBearer([("scada:site:info", "x")]),
)
@api_schema
def get_site_info(request, site_id: int):
    """获取信息"""

    return get_object_or_404(Site, id=site_id)


@router.put(
    "/{site_id}",
    response=SiteOut,
    auth=AuthBearer([("scada:site:update", "x")]),
)
@api_schema
def update_site(request, site_id: int, payload: SiteIn):
    """修改信息"""

    site = get_object_or_404(Site, id=site_id)
    site.name = payload.name
    site.contact = payload.contact
    site.mobile = payload.mobile
    site.status = payload.status
    site.remark = payload.remark
    site.longitude = payload.longitude
    site.latitude = payload.latitude
    site.save()
    return site


@router.delete(
    "/{site_id}",
    response=str,
    auth=AuthBearer([("scada:site:delete", "x")]),
)
@api_schema
def delete_site(request, site_id: int):
    """修改信息"""

    site = get_object_or_404(Site, id=site_id)
    site.delete()
    return "Ok"


@router.post(
    "/{site_id}/statistic",
    response=SiteStatisticOut,
    auth=AuthBearer([("scada:site:create", "x")]),
)
@api_schema
def create_statistic(request, site_id: int, payload: SiteStatisticIn):
    """创建站点统计变量"""

    site = get_object_or_404(Site, id=site_id)
    statistic = SiteStatistic(
        site_id=site_id, **payload.dict(exclude={"variable_ids": True})
    )
    statistic.save()

    statistic.variables.set(payload.variable_ids)

    output = SiteStatisticOut.from_orm(statistic)
    output.variable_ids = [v.id for v in statistic.variables.all()]

    return output


@router.get(
    "/{site_id}/statistic",
    response=SiteStatisticValueOut,
    auth=AuthBearer([("scada:site:get", "x")]),
)
@api_schema
def get_statistic_value(
    request, site_id: int, statistic_id: int = None, statistic_name: str = None
):
    """计算统计值并返回"""

    if statistic_id:
        statistic = get_object_or_404(SiteStatistic, id=statistic_id)
    elif statistic_name:
        statistic = SiteStatistic.objects.filter(
            site_id=site_id, name=statistic_name
        ).first()
        if not statistic:
            # 通过名字找不到统计量就直接返回0
            return SiteStatisticValueOut(id=-1, name=statistic_name)
    else:
        raise HttpError(400, "指定statistic_id或指定statistic_name")

    output = SiteStatisticValueOut.from_orm(statistic)

    values = []
    timestamp = 0

    for v in statistic.variables.all():
        output.variable_ids.append(v.id)

        # 查询字符串
        query_str = "grm_" + v.module.module_number + "_gauge"
        query_str += '{name="' + v.name + '"}'

        # 记得编码url参数
        query_params = urlencode({"query": query_str})
        query_resp = requests.get(
            f"{settings.PROMETHEUS_URL}/api/v1/query?{query_params}",
            timeout=(3, 5),
        )
        if query_resp.status_code != 200:
            continue

        query_data = query_resp.json()

        if query_data["status"] != "success":
            continue

        for result in query_data["data"]["result"]:
            timestamp = result["value"][0]
            values.append(float(result["value"][1]))

    output.value = sum(values)
    output.timestamp = timestamp
    return output


@router.get(
    "/{site_id}/statistic/options",
    response=list[SiteStatisticOut],
    auth=AuthBearer([("scada:site:get", "x")]),
)
@api_schema
def list_statistic(request, site_id: int):
    """获取列表"""
    statistic = SiteStatistic.objects.filter(site_id=site_id)
    outputs = []

    for s in statistic:
        o = SiteStatisticOut.from_orm(s)
        o.variable_ids = [v.id for v in s.variables.all()]
        outputs.append(o)

    return outputs


@router.put(
    "/statistic/{statistic_id}",
    response=SiteStatisticOut,
    auth=AuthBearer([("scada:site:create", "x")]),
)
@api_schema
def update_statistic(request, statistic_id: int, payload: SiteStatisticIn):
    """更新统计值配置"""

    statistic = get_object_or_404(SiteStatistic, id=statistic_id)
    statistic.name = payload.name
    statistic.method = payload.method
    statistic.save()

    statistic.variables.set(payload.variable_ids)

    output = SiteStatisticOut.from_orm(statistic)
    output.variable_ids = [v.id for v in statistic.variables.all()]
    return output


@router.delete(
    "/statistic/{statistic_id}",
    response=str,
    auth=AuthBearer([("scada:site:create", "x")]),
)
@api_schema
def delete_statistic(request, statistic_id: int):
    """删除统计值"""

    statistic = get_object_or_404(SiteStatistic, id=statistic_id)
    statistic.delete()

    return "Ok"


@router.post(
    "/{site_id}/videosource",
    response=SiteVideoSourceOptionOut,
    auth=AuthBearer([("scada:site:create", "x")]),
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
    auth=AuthBearer([("scada:site:get", "x")]),
)
@api_schema
def list_videosource(request, site_id: int):
    """列出视频源"""

    return SiteVideoSource.objects.filter(site_id=site_id).all()


@router.get(
    "/videosource/{videosource_id}",
    response=SiteVideoSourceOut,
    auth=AuthBearer([("scada:site:get", "x")]),
)
@api_schema
def get_videosource(request, videosource_id: int):
    """调用视频源接口获取播放地址和截图"""

    svs = get_object_or_404(SiteVideoSource, id=videosource_id)
    output = SiteVideoSourceOut.from_orm(svs)

    try:
        output.capture = get_capture_url(device_serial=svs.device_id, channel_no=int(svs.channel))
        output.video_source = get_video_url(device_serial=svs.device_id, channel_no=int(svs.channel))
        output.token = get_accecc_token()
    except Exception as e:
        # raise HttpError(500, f"获取视频截图或播放地址错误: {e}")
        pass

    return output


@router.delete(
    "/videosource/{videosource_id}",
    response=str,
    auth=AuthBearer([("scada:site:create", "x")]),
)
@api_schema
def delete_videosource(request, videosource_id: int):
    """删除通道"""

    svs = get_object_or_404(SiteVideoSource, id=videosource_id)
    svs.delete()
    return "Ok"
