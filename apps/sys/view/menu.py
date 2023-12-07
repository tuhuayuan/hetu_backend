from django.shortcuts import get_object_or_404
from ninja import Router

from apps.sys.models import Menu
from casbin_adapter.enforcer import enforcer
from apps.sys.schemas import (
    MenuIn,
    MenuInfoOut,
    MenuTreeOptionOut,
    MenuTreeOut,
    MenuTreeRouterOut,
    MenuType,
)
from apps.sys.utils import AuthBearer
from utils.schema.base import api_schema

router = Router()


@router.post(
    "",
    response=MenuInfoOut,
    auth=AuthBearer([("sys:menu:add", "x")]),
)
@api_schema
def create_menu(request, payload: MenuIn):
    """创建菜单"""

    m = Menu(**payload.dict())
    m.save()
    return m


@router.get(
    "/options",
    response=list[MenuTreeOptionOut],
    exclude_none=True,
    auth=AuthBearer([("sys:menu:edit", "x")]),
)
@api_schema
def get_menu_option_tree(request):
    """获取选项树"""

    def _get_menu_and_child(menu: Menu):
        current_data = MenuTreeOptionOut.from_orm(menu)

        children = Menu.objects.filter(parent_id=current_data.id).all()
        if children:
            current_data.children = []

        # 递归
        for child in children:
            child_data = _get_menu_and_child(child)
            if child_data:
                current_data.children.append(child_data)
        return current_data

    root_menus = Menu.objects.filter(parent_id=0).all()
    root_menus_data: MenuTreeOptionOut = []
    for m in root_menus:
        menu_data = _get_menu_and_child(m)
        root_menus_data.append(menu_data)

    return root_menus_data


@router.get("/routers", response=list[MenuTreeRouterOut], exclude_none=True)
@api_schema
def get_menu_router_tree(request):
    """获取路由树"""

    def _to_camel_case(s: str):
        parts = s.split("-")
        return "".join(part.title() for part in parts)

    def _get_menu_and_child(menu: Menu, parent_name=""):
        roles = [r.code for r in menu.roles.all()]

        meta = MenuTreeRouterOut.RouterMeta(
            title=menu.name,
            icon=menu.icon,
            hidden=not bool(menu.visible),
            roles=roles,
            keep_alive=True,
        )

        current_router = MenuTreeRouterOut(
            path=menu.path, component=menu.component, meta=meta
        )

        # 构建 name，如果有父级名称则结合父级名称和当前 path 的驼峰形式来确保唯一性
        if menu.menu_type == MenuType.MENU:
            combined_name = (parent_name + '-' + menu.path).replace("/", "-")
            current_router.name = _to_camel_case(combined_name)
        else:
            current_router.name = menu.path

        children = (
            Menu.objects.filter(parent_id=menu.id).exclude(menu_type="BUTTON").all()
        )
        if children:
            current_router.children = []

        # 递归
        for child in children:
            child_router = _get_menu_and_child(child, current_router.name)
            if child_router:
                current_router.children.append(child_router)
        return current_router

    root_menus = Menu.objects.filter(parent_id=0).exclude(menu_type="BUTTON").all()
    root_menus_router: MenuTreeRouterOut = []
    for m in root_menus:
        menu_router = _get_menu_and_child(m)
        root_menus_router.append(menu_router)
    return root_menus_router


@router.get(
    "/{menu_id}",
    response=MenuInfoOut,
    auth=AuthBearer([("sys:menu:edit", "x")]),
)
@api_schema
def get_menu_info(request, menu_id: int):
    """获取菜单信息"""

    return get_object_or_404(Menu, id=menu_id)


@router.put(
    "/{menu_id}",
    response=MenuInfoOut,
    auth=AuthBearer([("sys:menu:edit", "x")]),
)
@api_schema
def update_menu_info(request, menu_id: int, payload: MenuIn):
    """修改菜单信息"""

    menu = get_object_or_404(Menu, id=menu_id)

    if menu.perm:
        # 加载持久化
        enforcer.load_policy()

        if not payload.perm:
            # 清除菜单权限
            enforcer.remove_filtered_policy(1, menu.perm)
        elif menu.perm != payload.perm:
            # 更换了权限标识
            policies = enforcer.get_filtered_policy(1, menu.perm)
            enforcer.remove_filtered_policy(1, menu.perm)
            for p in policies:
                enforcer.add_policy(p[0], payload.perm, p[2])

    # 偷个懒
    for key, value in payload.dict().items():
        setattr(menu, key, value)

    menu.save()
    return menu


@router.patch(
    "/{menu_id}",
    response=MenuInfoOut,
    auth=AuthBearer([("sys:menu:edit", "x")]),
)
@api_schema
def change_meun_visible(request, menu_id: int, visible: bool):
    """修改菜单可见性"""

    m = get_object_or_404(Menu, id=menu_id)
    m.visible = visible
    m.save()
    return m


@router.get(
    "",
    response=list[MenuTreeOut],
    auth=AuthBearer([("sys:menu:edit", "x")]),
)
@api_schema
def get_menu_tree(request, visible: int = None, keyword: str = None):
    """获取菜单树列表"""

    def _get_filter(parent_id):
        filter_kwargs = {"parent_id": parent_id}
        if visible is not None:
            filter_kwargs["visible"] = bool(visible)
        if keyword is not None:
            filter_kwargs["name__icontains"] = keyword
        return filter_kwargs

    def _get_menu_and_child(menu: Menu):
        current_data = MenuTreeOut.from_orm(menu)

        children = Menu.objects.filter(**_get_filter(current_data.id)).all()
        for child in children:
            child_data = _get_menu_and_child(child)
            if child_data:
                current_data.children.append(child_data)
        return current_data

    root_menus = Menu.objects.filter(**_get_filter(None)).all()
    root_menus_data: MenuTreeOut = []
    for m in root_menus:
        menu_data = _get_menu_and_child(m)
        root_menus_data.append(menu_data)

    return root_menus_data


@router.delete(
    "/{menu_id}",
    response=str,
    auth=AuthBearer([("sys:menu:delete", "x")]),
)
@api_schema
def delete_menu(request, menu_id: int):
    """删除菜单"""

    # 删除菜单
    menu = get_object_or_404(Menu, id=menu_id)
    menu.delete()

    if menu.perm:
        # 清除菜单权限
        enforcer.load_policy()
        enforcer.remove_filtered_policy(1, menu.perm)

    return "Ok"
