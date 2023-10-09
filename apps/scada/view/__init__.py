from ninja import Router

from apps.scada.view.module import router as module_router
from apps.scada.view.variable import router as variable_router
from apps.scada.view.collector import router as collector_router
from apps.scada.view.alert import router as alert_router

router = Router()
router.add_router("/module", module_router)
router.add_router("/variable", variable_router)
router.add_router("/collector", collector_router)
router.add_router("/aler", alert_router)
