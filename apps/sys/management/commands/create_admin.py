from django.core.management.base import BaseCommand
from apps.sys.models import Department, Role, User
from apps.sys.utils import get_password


class Command(BaseCommand):
    help = "Create admin user with provided password, assign to ADMIN role and assign to provided department"

    def add_arguments(self, parser):
        parser.add_argument("password", type=str, help="Password for the admin user")
        parser.add_argument(
            "department", type=str, help="Name of the department for the admin user"
        )

    def handle(self, *args, **options):
        # 获取参数
        password = options["password"]
        department_name = options["department"]

        if User.objects.filter(username="admin").first():
            self.stdout.write(self.style.ERROR("admin existed."))
            return

        # 创建 ADMIN 角色
        admin_role, created = Role.objects.get_or_create(
            name="管理员", code="ADMIN", sort=1
        )

        # 创建部门或获取现有部门
        admin_department, created = Department.objects.get_or_create(
            name=department_name
        )

        # 创建 admin 用户
        admin = User(
            username="admin",
            password=get_password(password),
            dept=admin_department,
        )
        admin.save()
        # 将 ADMIN 角色分配给 admin 用户
        admin.roles.add(admin_role)

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully created admin user, assigned to ADMIN role and assigned to the specified department"
            )
        )
