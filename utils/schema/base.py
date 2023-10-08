from functools import partial, wraps
from typing import Any, Callable, Optional

from ninja import Schema
from ninja.compatibility.util import get_args as get_collection_args
from ninja.constants import NOT_SET
from ninja.errors import ConfigError, HttpError
from ninja.operation import Operation
from ninja.signature.details import is_collection_type


class BaseSchemaOut(Schema):
    """API响应基础类"""

    # success或者error
    status: str
    # 错误也可能包含数据
    data: Any
    # 如果是error则包含错误内容
    error: str = ""
    # 错误类型
    error_type: str = ""


def api_schema(func_view) -> Callable:
    """
    包装API格式
    """

    return _inject_api_schema(func_view)


def _inject_api_schema(func: Callable) -> Callable:
    @wraps(func)
    def api_view(*args: tuple[Any], **kwargs: Any) -> Any:
        return BaseSchemaOut(status="success", data=func(*args, **kwargs))

    # 修改响应类型
    api_view._ninja_contribute_to_operation = partial(_make_api_schema)

    return api_view


def _make_api_schema(op: Operation) -> None:
    """动态构建正确的API返回类型"""

    item_schema = None

    for code, resp_model in op.response_models.items():
        if resp_model is None or resp_model is NOT_SET or code != 200:
            continue

        item_schema = resp_model.__annotations__["response"]
        break

    if not resp_model:
        raise ConfigError(
            f'"{op.view_func}" has no response (e.g. response=SomeSchema)'
        )

    if is_collection_type(item_schema):
        naming_schema = get_collection_args(item_schema)[0]
        data_schema = list[naming_schema]
    else:
        naming_schema = item_schema
        data_schema = item_schema

    # 输出的Schema采用Out作为后缀命名
    try:
        new_schema_name = f"{naming_schema.__name__}Out"
    except AttributeError:
        new_schema_name = (
            f"{str(naming_schema).replace('.', '_')}Out"  # typing.Any case
        )

    # 动态申明一个新的BaseSchemaOut的子类

    new_schema = type(
        new_schema_name,
        (BaseSchemaOut,),
        {
            "__annotations__": {"data": Optional[data_schema]},  # type: ignore
        },
    )  # typing: ignore

    # 修改视图的响应模型
    op.response_models[200] = op._create_response_model(new_schema)
