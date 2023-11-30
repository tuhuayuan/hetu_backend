from datetime import datetime, timezone

from django.shortcuts import get_object_or_404
from ninja import Router
from django.db.models import Q
from apps.sys.models import Department
from apps.sys.schemas import (
    DepartmentIn,
    DepartmentListOut,
    DepartmentOptionOut,
    DepartmentOut,
    DepartmentUpdateIn,
)
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema

router = Router()


@router.post(
    "",
    response=DepartmentOut,
    auth=AuthBearer([("sys:dept:add", "x")]),
)
@api_schema
def create_dept(request, payload: DepartmentIn):
    """创建部门"""

    d = Department(create_time=datetime.now(timezone.utc), **payload.dict())
    d.save()
    return d


@router.get(
    "/options",
    response=list[DepartmentOptionOut],
    auth=AuthBearer([("sys:dept:edit", "x")]),
    exclude_none=True,
)
@api_schema
def get_dept_option_list(request):
    """获取部门选项树状图"""

    def _get_children(current: Department):
        current_out = DepartmentOptionOut.from_orm(current)
        subs = Department.objects.filter(parent_id=current.id)
        if subs:
            current_out.children = []
            for sub_dept in subs:
                sub_out = _get_children(sub_dept)
                current_out.children.append(sub_out)
        return current_out

    options_out: list[DepartmentOptionOut] = []
    depts = Department.objects.filter(parent_id=None).all()
    for d in depts:
        options_out.append(_get_children(d))

    return options_out


@router.get(
    "",
    response=list[DepartmentListOut],
    auth=AuthBearer([("sys:dept:edit", "x")]),
)
@api_schema
def get_dept_list(request, status: int = None, keywords: str = None):
    """获取部门列表"""
    output: list[DepartmentListOut] = []
    depts = Department.objects.all()

    if keywords:
        depts = depts.filter(Q(name__icontains=keywords))

    if status:
        depts = depts.filter(status=status)

    def _get_children_out(dept):
        current_out = DepartmentListOut.from_orm(dept)

        child_depts = depts.filter(parent_id=dept.id)
        if child_depts:
            for child in child_depts:
                child_out = _get_children_out(child)
                current_out.children.append(child_out)
        return current_out

    ids = set([d.id for d in depts.all()])
    root_depts = [
        dept for dept in depts.all() if not dept.parent_id or dept.parent_id not in ids
    ]
    
    for dept in root_depts:
        dept_out = _get_children_out(dept)
        output.append(dept_out)
    return output


@router.get(
    "/{dept_id}",
    response=DepartmentOut,
    auth=AuthBearer([("sys:dept:edit", "x")]),
)
@api_schema
def get_dept_info(request, dept_id: int):
    """获取部门信息"""

    return get_object_or_404(Department, id=dept_id)


@router.put(
    "/{dept_id}",
    response=DepartmentOut,
    auth=AuthBearer([("sys:dept:edit", "x")]),
)
@api_schema
def update_dept(request, dept_id: int, payload: DepartmentUpdateIn):
    """更新部门信息"""

    d = get_object_or_404(Department, id=dept_id)
    d.sort = payload.sort
    d.description = payload.description
    d.status = payload.status
    d.parent_id = payload.parent_id
    d.save()
    return d


@router.delete('/{dept_id}', response=str, auth=AuthBearer([("sys:dept:delete", "x")]))
@api_schema
def delete_dept(request, dept_id: int):
    """删除部门"""

    d = get_object_or_404(Department, id=dept_id)
    d.delete()
    return 'Ok'
