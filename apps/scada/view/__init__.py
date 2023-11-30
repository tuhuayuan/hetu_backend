from ninja import Router

from apps.scada.view.module import router as module_router
from apps.scada.view.variable import router as variable_router
from apps.scada.view.collector import router as collector_router
from apps.scada.view.alert import router as alert_router
from apps.scada.view.site import router as site_router
from apps.scada.view.graph import router as graph_router
from apps.scada.view.videosource import router as videosource_router

router = Router()

# 资源路径风格的路由
router.add_router("/site", site_router)
router.add_router("/site", graph_router)
router.add_router("/site", module_router)
router.add_router("/site", variable_router)
router.add_router("/site", alert_router)
router.add_router("/site", collector_router)
router.add_router("/site", videosource_router)

# For prometheus
from apps.scada.view.collector import service_discover
from apps.scada.view.alert import create_notify

router.add_api_operation("/collector/sd", ['GET'], service_discover)
router.add_api_operation("/alert/notify", ['POST'], create_notify)

