# Generated by Django 4.2.5 on 2023-10-08 02:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sys', '0006_alter_menu_parent_alter_user_dept'),
    ]

    operations = [
        migrations.AlterField(
            model_name='menu',
            name='perm',
            field=models.CharField(max_length=255, null=True, unique=True),
        ),
    ]