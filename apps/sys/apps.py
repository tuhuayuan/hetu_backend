from django.apps import AppConfig
from django.conf import settings


class AuthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sys"

    def ready(self) -> None:
        from apps.sys.rolemanager import RoleManager

        setattr(settings, "CASBIN_ROLE_MANAGER", RoleManager())
