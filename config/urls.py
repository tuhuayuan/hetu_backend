"""
URL configuration for hetu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.urls import path
from ninja import NinjaAPI

from apps.scada.view import router as scada_router
from apps.sys.view import router as sys_router
from utils.schema.errors import set_default_exc_handlers

api = NinjaAPI(title="养殖污水智慧运营平台", version="v1")
set_default_exc_handlers(api)

api.add_router("scada/", scada_router)
api.add_router("sys/", sys_router)


urlpatterns = [
    path("api/", api.urls),
]
