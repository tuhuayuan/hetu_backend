from ninja import Router

from apps.sys.view.auth import router as auth_router
from apps.sys.view.dept import router as dept_router
from apps.sys.view.dict import router as dict_router
from apps.sys.view.menu import router as menu_router
from apps.sys.view.role import router as role_router
from apps.sys.view.user import router as user_router


router = Router()
router.add_router("/auth", auth_router)
router.add_router("/dept", dept_router)
router.add_router("/dict", dict_router)
router.add_router("/menu", menu_router)
router.add_router("/role", role_router)
router.add_router("/user", user_router)
