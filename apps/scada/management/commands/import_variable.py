from django.core.management.base import BaseCommand
from apps.scada.models import Module, Variable
import pandas as pd


class Command(BaseCommand):
    help = "Imports module variables from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("module_number", type=str, help="Module number")
        parser.add_argument("csv_file", type=str, help="CSV file path")

    def handle(self, *args, **options):
        # 获取参数
        module_number = options["module_number"]
        csv_file = options["csv_file"]

        def _save(row, module):
            v, created = Variable.objects.get_or_create(
                name=row["变量名"],
                group=row["变量组"],
                module_id=module.id,
            )
            v.rw = True
            v.local = False
            if row["变量类型"] == "整型":
                v.type = "I"
            elif row["变量类型"] == "浮点":
                v.type = "F"
            else:
                v.type = "B"
            v.save()
            return pd.Series([v.id, created])

        module = Module.objects.filter(module_number=module_number).first()
        if not module:
            self.stdout.write(self.style.ERROR("module not exits"))
            return

        # 使用 pandas 读取 CSV 文件
        columns = ["变量名", "变量类型", "变量组"]
        data = pd.read_csv(csv_file, usecols=columns)
        ids = data.apply(lambda r: _save(r, module), axis=1)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(ids)} variables, created {ids[1].sum()}"
            )
        )
