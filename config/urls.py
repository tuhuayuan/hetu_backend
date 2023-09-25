"""
URL configuration for hetu project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from ninja import NinjaAPI

from apps.grm.views import router as grm_router
from apps.exporter.views import router as exporter_router
from apps.alert.views import router as alert_router

api = NinjaAPI(title='养殖污水智慧运营平台')
api.add_router('grm/', grm_router)
api.add_router('exporter/', exporter_router)
api.add_router('alert/', alert_router)


urlpatterns = [
    path('api/', api.urls),
]
