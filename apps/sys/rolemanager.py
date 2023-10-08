import logging

from casbin.rbac import RoleManager as RM

from apps.sys.models import Role, User


class RoleManager(RM):
    """实现角色管理器"""

    def __init__(self):
        self.logger = logging.getLogger("casbin.role")

    def clear(self):
        pass

    def add_link(self, name1, name2, *domain):
        pass

    def delete_link(self, name1, name2, *domain):
        pass

    def has_link(self, name1, name2, *domain):
        """判断username是否属于rolename的角色"""
        if name1 == name2:
            return True
        
        u = User.objects.filter(username=name1).first()
        if not u:
            return False
        return name2 in [r.code for r in u.roles.all()]

    def get_roles(self, name, *domain):
        """获取用户所属角色"""

        u = User.objects.filter(username=name).first()
        if not u:
            return []

        return [r.code for r in u.roles.all()]

    def get_users(self, name, *domain):
        """获取角色下所有用户"""

        r = Role.objects.filter(code=name).first()
        if not r:
            return []

        return [u.username for u in r.user_set.all()]

    def print_roles(self):
        pass
