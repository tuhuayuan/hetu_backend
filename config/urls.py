"""
URL configuration for hetu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
import json
from django.urls import path
from ninja import NinjaAPI
from django.http import HttpResponse
from apps.scada.view import router as scada_router
from apps.sys.view import router as sys_router
from utils.schema.errors import set_default_exc_handlers
from ninja.renderers import JSONRenderer


class UTF8JSONRenderer(JSONRenderer):
    json_dumps_params = {"ensure_ascii": False}


api = NinjaAPI(title="养殖污水智慧运营平台", version="v1", renderer=UTF8JSONRenderer())
set_default_exc_handlers(api)

api.add_router("scada/", scada_router)
api.add_router("sys/", sys_router)


def healthy(request):
    return HttpResponse("Ok")


urlpatterns = [
    path("api/", api.urls),
    path("-/healthy", healthy, name="healthy"),
]
