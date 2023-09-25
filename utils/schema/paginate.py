"""
参照ninja官方的paginate，按照自己的API接口返回格式修改而成。
https://django-ninja.rest-framework.com/guides/response/pagination/#creating-custom-pagination-class
"""

from functools import partial, wraps
from typing import Any, Callable, Tuple, Optional

from django.conf import settings
from django.db.models import QuerySet
from ninja import Field, Query, Schema
from ninja.compatibility.util import get_args as get_collection_args
from ninja.constants import NOT_SET
from ninja.errors import ConfigError, HttpError
from ninja.operation import Operation
from ninja.signature.details import is_collection_type

from utils.schema.base import BaseSchemaOut


class BasePagination:
    """基础的分页器"""

    items_attribute = 'items'
    InputSource = Query(...)

    class Input(Schema):
        """分页请求参数"""
        limit: int = Field(settings.PAGINATION_PER_PAGE, ge=1)
        offset: int = Field(0, ge=0)

    class Output(Schema):
        """分页数据"""
        items: list[Any]
        count: int

    def paginate_queryset(self, queryset: QuerySet, pagination: Any) -> None:
        offset = pagination.offset
        limit: int = pagination.limit
        return {
            "items": queryset[offset: offset + limit],
            "count": self._items_count(queryset),
        }

    def _items_count(self, queryset: QuerySet) -> int:
        try:
            return queryset.all().count()
        except AttributeError:
            return len(queryset)


def api_paginate(view_func) -> Callable:
    """分页修饰器"""

    return _inject_pagination(view_func)


def _inject_pagination(func: Callable) -> Callable:
    paginator = BasePagination()

    @wraps(func)
    def view_with_pagination(*args: Tuple[Any], **kwargs: Any) -> Any:
        # 这个参数是我们通过_ninja_contribute_args放进去的Schema
        pagination_params = kwargs.pop("base_pagination")

        # 执行被封装的View，items是一个collection
        try:        
            items = func(*args, **kwargs)

            # 执行实际的分页逻辑
            result = paginator.paginate_queryset(
                items, pagination=pagination_params
            )
            result[paginator.items_attribute] = list(result[paginator.items_attribute])
    
            return BaseSchemaOut(status='success', data=result)
        except HttpError as e:
            return BaseSchemaOut(status='error', data=None, error=str(e))
        except Exception as e:
            # 输出错误日志
            print(e)
            return BaseSchemaOut(status='error', data=None, error='未处理异常')

    # 添加分页参数
    view_with_pagination._ninja_contribute_args = [  # type: ignore
        (
            # 参数名
            "base_pagination",
            # 参数Schema
            paginator.Input,
            # 参数
            paginator.InputSource,
        ),
    ]

    # 修改响应类型
    if paginator.Output:
        view_with_pagination._ninja_contribute_to_operation = partial(  # type: ignore
            _make_response_paginated, paginator
        )

    return view_with_pagination


def _make_response_paginated(paginator: BasePagination, op: Operation) -> None:
    """自动转换响应的Schema"""

    status_code, item_schema = _find_collection_response(op)

    # 输出的Schema采用Paged前缀命名
    try:
        new_item_name = f"Paged{item_schema.__name__}"
    except AttributeError:
        new_item_name = f"Paged{str(item_schema).replace('.', '_')}"  # typing.Any case

    #  动态申明一个新的Schema
    new_item_schema = type(
        new_item_name,
        (paginator.Output,),
        {
            "__annotations__": {paginator.items_attribute: list[item_schema]},  # type: ignore
        },
    )  # typing: ignore

    # 动态申明一个新的BaseSchemaOut的子类
    new_base_schema = type(
        new_item_name + 'Out',
        (BaseSchemaOut,),
        {
            "__annotations__": {'data': Optional[new_item_schema]},  # type: ignore
        },
    )  # typing: ignore

    response = op._create_response_model(new_base_schema)

    # 修改视图的响应模型
    op.response_models[status_code] = response


def _find_collection_response(op: Operation) -> Tuple[int, Any]:
    """获取需要分页的视图的响应类型，必须是list类型
    返回对应的状态码和Schema类型
    """

    for code, resp_model in op.response_models.items():
        if resp_model is None or resp_model is NOT_SET:
            continue

        model = resp_model.__annotations__["response"]
        if is_collection_type(model):
            item_schema = get_collection_args(model)[0]
            return code, item_schema

    raise ConfigError(
        f'"{op.view_func}" has no collection response (e.g. response=List[SomeSchema])'
    )
