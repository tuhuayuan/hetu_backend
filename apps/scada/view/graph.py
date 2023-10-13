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
    "",
    response=GraphOut,
    auth=AuthBearer([("scada:graph:create", "x")]),
)
@api_schema
def create_graph(request, payload: GraphIn):
    """创建组态图"""

    g = Graph(**payload.dict())
    g.save()
    return g


@router.get(
    "/options",
    response=list[GraphOptionOut],
    auth=AuthBearer([("scada:graph:list", "x")]),
)
@api_schema
def get_graph_option_list(request):
    """获取组态图选项列表"""

    return Graph.objects.all()


@router.get(
    "",
    response=list[GraphOut],
    auth=AuthBearer([("scada:graph:list", "x")]),
)
@api_paginate
def get_graph_list(request, site_id: int = None, keywords: str = None):
    """获取组态图列表（包含数据）"""

    gs = Graph.objects.all()

    if site_id:
        gs = gs.filter(site_id=site_id)

    if keywords:
        gs = gs.filter(Q(name__icontains=keywords))

    return gs


@router.get(
    "/{graph_id}",
    response=GraphOut,
    auth=AuthBearer([("scada:graph:info", "x")]),
)
@api_schema
def get_graph_list(request, graph_id: int):
    """获取组态图"""

    return get_object_or_404(Graph, id=graph_id)


@router.put(
    "/{graph_id}",
    response=GraphOut,
    auth=AuthBearer([("scada:graph:update", "x")]),
)
@api_schema
def update_graph(request, graph_id: int, payload: GraphIn):
    """更新或则保存"""

    g = get_object_or_404(Graph, id=graph_id)
    g.name = payload.name
    g.status = payload.status
    g.data = payload.data
    g.remark = payload.remark
    g.site_id = payload.site_id
    g.save()
    return g


@router.delete(
    "/{graph_id}",
    response=str,
    auth=AuthBearer([("scada:graph:delete", "x")]),
)
@api_schema
def delete_graph(request, graph_id: int):
    """删除图"""

    g = get_object_or_404(Graph, id=graph_id)
    g.delete()
    return "Ok"
