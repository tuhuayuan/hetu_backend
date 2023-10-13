from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.scada.models import Site
from apps.scada.schema.site import SiteIn, SiteOptionOut, SiteOut
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
