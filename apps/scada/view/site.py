from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from ninja import Router

from apps.scada.models import Site, SiteStatistic
from apps.scada.schema.site import (
    SITE_PERMIT,
    SiteIn,
    SiteOptionOut,
    SiteOut,
    SitePermit,
    SiteStatisticIn,
    SiteStatisticOut,
    SiteStatisticValueOut,
)
from apps.scada.utils.promql import query_prometheus
from apps.sys.utils import AuthBearer, get_enforcer
from apps.sys.models import User
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.get(
    "/{site_id}/permit",
    response=list[SitePermit],
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
        ]
    ),
)
@api_schema
def get_permit_list(request, site_id: int):
    enforcer = get_enforcer()
    policies = enforcer.get_filtered_policy(1, f"scada:site:permit:{site_id}")
    permit: dict[int, str] = {}

    for username, _, permission in policies:
        user = User.objects.filter(username=username).values("id").first()
        if not user:
            continue
        user_id = user["id"]
        if permission == "w":
            permit[user_id] = permission
        elif permission == "r" and user_id not in permit:
            permit[user_id] = permission

    output = [
        SitePermit(user_id=user_id, permit=SITE_PERMIT(permission), site_id=site_id)
        for user_id, permission in permit.items()
    ]

    return output


@router.get(
    "/permit/{user_id}",
    response=list[SitePermit],
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
        ]
    ),
)
@api_schema
def get_permit_by_user(request, user_id: int):
    """获取用户授权的列表"""

    user = get_object_or_404(User, id=user_id)
    enforcer = get_enforcer()
    policies = [
        policy
        for policy in enforcer.get_filtered_policy(0, user.username)
        if policy[1].startswith("scada:site:permit:")
    ]
    permit: dict[int, str] = {}

    for _, target, permission in policies:
        site_id = target.split(":")[-1]
        if permission == "w":
            permit[site_id] = permission
        elif permission == "r" and site_id not in permit:
            permit[site_id] = permission

    output = [
        SitePermit(user_id=user_id, permit=SITE_PERMIT(permission), site_id=site_id)
        for site_id, permission in permit.items()
    ]

    return output


@router.post(
    "/{site_id}/permit",
    response=str,
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
        ]
    ),
)
@api_schema
def grand_permits(request, site_id: int, payload: SitePermit):
    """站点权限"""

    enforcer = get_enforcer()
    user = get_object_or_404(User, id=payload.user_id)

    if payload.permit == SITE_PERMIT.WRITE:
        enforcer.add_policy(user.username, f"scada:site:permit:{site_id}", "w")
        enforcer.add_policy(user.username, f"scada:site:permit:{site_id}", "r")
    elif payload.permit == SITE_PERMIT.READ:
        enforcer.remove_filtered_policy(
            0, user.username, f"scada:site:permit:{site_id}"
        )
        enforcer.add_policy(user.username, f"scada:site:permit:{site_id}", "r")
    else:
        enforcer.remove_filtered_policy(
            0, user.username, f"scada:site:permit:{site_id}"
        )
    return "Ok"


@router.post(
    "",
    response=SiteOut,
    auth=AuthBearer(
        [
            ("scada:site:add", "x"),
        ]
    ),
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
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
        ],
    ),
)
@api_schema
def get_site_option_list(request):
    """选项列表"""

    enforcer = get_enforcer()

    policies = enforcer.get_filtered_policy(0, request.auth["username"])
    permit_ids = [
        int(policy[1].split(":")[-1])
        for policy in policies
        if policy[1].startswith("scada:site:permit:")
    ]
    # return Site.objects.filter(id__in=permit_ids)
    return Site.objects.all()


@router.get(
    "",
    response=list[SiteOut],
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
        ]
    ),
)
@api_paginate
def get_site_list(request, keywords: str = None):
    """获取信息列表, 不检查权限"""

    sites = Site.objects.all()

    if keywords:
        sites = sites.filter(
            Q(name__icontains=keywords) | Q(contact__icontains=keywords)
        )

    return sites


@router.get(
    "/{site_id}",
    response=SiteOut,
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_site_info(request, site_id: int):
    """获取信息"""

    return get_object_or_404(Site, id=site_id)


@router.put(
    "/{site_id}",
    response=SiteOut,
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
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
    auth=AuthBearer(
        [
            ("scada:site:delete", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
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
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
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
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
        ]
    ),
)
@api_schema
def get_statistic_value(
    request, site_id: int, statistic_id: int = None, statistic_name: str = None
):
    """计算统计值并返回"""

    if statistic_id:
        statistic = get_object_or_404(SiteStatistic, id=statistic_id, site_id=site_id)
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

        try:
            query_data = query_prometheus(query_str)
        except Exception:
            continue

        for result in query_data["data"]["result"]:
            timestamp = result["value"][0]
            values.append(float(result["value"][1]))

    # 目前只支持累加
    output.value = sum(values)
    output.timestamp = timestamp
    return output


@router.get(
    "/{site_id}/statistic/options",
    response=list[SiteStatisticOut],
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:info", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
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
    "/{site_id}/statistic/{statistic_id}",
    response=SiteStatisticOut,
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def update_statistic(
    request, site_id: int, statistic_id: int, payload: SiteStatisticIn
):
    """更新统计值配置"""

    statistic = get_object_or_404(SiteStatistic, id=statistic_id, site_id=site_id)
    statistic.name = payload.name
    statistic.method = payload.method
    statistic.save()

    statistic.variables.set(payload.variable_ids)

    output = SiteStatisticOut.from_orm(statistic)
    output.variable_ids = [v.id for v in statistic.variables.all()]
    return output


@router.delete(
    "/{site_id}/statistic/{statistic_id}",
    response=str,
    auth=AuthBearer(
        [
            ("scada:site:edit", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def delete_statistic(request, site_id: int, statistic_id: int):
    """删除统计值"""

    statistic = get_object_or_404(SiteStatistic, id=statistic_id, site_id=site_id)
    statistic.delete()

    return "Ok"
