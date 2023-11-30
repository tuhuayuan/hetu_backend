from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router

from apps.scada.models import Graph
from apps.scada.schema.graph import GraphIn, GraphOptionOut, GraphOut
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema
from utils.schema.paginate import api_paginate

router = Router()


@router.post(
    "/{site_id}/graph",
    response=GraphOut,
    auth=AuthBearer(
        [
            ("scada:graph:create", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def create_graph(request, site_id: int, payload: GraphIn):
    """创建组态图"""

    g = Graph(**payload.dict())
    g.site_id = site_id
    g.save()
    return g


@router.get(
    "/{site_id}/graph/options",
    response=list[GraphOptionOut],
    auth=AuthBearer(
        [
            ("scada:graph:options", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_graph_option_list(request, site_id: int):
    """获取组态图选项列表"""

    return Graph.objects.filter(site_id=site_id)


@router.get(
    "/{site_id}/graph",
    response=list[GraphOut],
    auth=AuthBearer(
        [
            ("scada:graph:list", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_paginate
def get_graph_list(request, site_id: int, keywords: str = None):
    """获取组态图列表（包含数据）"""

    gs = Graph.objects.filter(site_id=site_id)

    if keywords:
        gs = gs.filter(Q(name__icontains=keywords))

    return gs.order_by("-order")


@router.get(
    "/{site_id}/graph/{graph_id}",
    response=GraphOut,
    auth=AuthBearer(
        [
            ("scada:graph:get", "x"),
            ("scada:site:permit:{site_id}", "r"),
        ]
    ),
)
@api_schema
def get_graph_info(request, site_id: int, graph_id: int):
    """获取组态图"""

    return get_object_or_404(Graph, id=graph_id, site_id=site_id)


@router.put(
    "/{site_id}/graph/{graph_id}",
    response=GraphOut,
    auth=AuthBearer(
        [
            ("scada:graph:update", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def update_graph(request, site_id: int, graph_id: int, payload: GraphIn):
    """更新或则保存"""

    g = get_object_or_404(Graph, id=graph_id, site_id=site_id)
    g.name = payload.name
    g.status = payload.status
    g.data = payload.data
    g.remark = payload.remark
    g.order = payload.order
    g.save()
    return g


@router.delete(
    "/{site_id}/graph/{graph_id}",
    response=str,
    auth=AuthBearer(
        [
            ("scada:graph:delete", "x"),
            ("scada:site:permit:{site_id}", "w"),
        ]
    ),
)
@api_schema
def delete_graph(request, site_id: int, graph_id: int):
    """删除图"""

    g = get_object_or_404(Graph, id=graph_id, site_id=site_id)
    g.delete()
    return "Ok"
