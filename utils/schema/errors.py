from functools import partial
import logging
import traceback

from django.conf import settings
from django.http import Http404, HttpResponse
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, HttpError, ValidationError

from utils.schema.base import BaseSchemaOut

logger = logging.getLogger("django")


def set_default_exc_handlers(api: NinjaAPI) -> None:
    """设置默认错误处理器"""

    api.add_exception_handler(Exception, partial(nothandle_error, api=api))
    api.add_exception_handler(Http404, partial(notfound_error, api=api))
    api.add_exception_handler(HttpError, partial(httpstatus_error, api=api))
    api.add_exception_handler(ValidationError, partial(validation_error, api=api))
    api.add_exception_handler(
        AuthenticationError, partial(authentication_error, api=api)
    )


def validation_error(request, exc: ValidationError, api: NinjaAPI):
    """参数验证错误"""
    return api.create_response(
        request,
        BaseSchemaOut(status="error", data=exc.errors, error="输入参数错误"),
        status=422,
    )


def authentication_error(request, exc: AuthenticationError, api: NinjaAPI):
    """认证失败错误"""

    return api.create_response(
        request, BaseSchemaOut(status="error", data=None, error="认证失败"), status=401
    )


def notfound_error(request, exc: Exception, api: NinjaAPI):
    """处理django的404"""

    msg = "对象不存在"
    if settings.DEBUG:
        msg += f": {exc}"

    return api.create_response(
        request, BaseSchemaOut(status="error", data=None, error=msg), status=404
    )


def httpstatus_error(request, exc: HttpError, api: NinjaAPI):
    """处理HttpError异常"""

    return api.create_response(
        request,
        BaseSchemaOut(status="error", data=None, error=str(exc)),
        status=exc.status_code,
    )


def nothandle_error(request, exc: Exception, api: NinjaAPI):
    """处理任何没处理的异常"""
    if not settings.DEBUG:
        raise exc

    logger.exception(exc)
    tb = traceback.format_exc()
    return api.create_response(
        request, BaseSchemaOut(status="error", data=None, error=tb), status=500
    )
