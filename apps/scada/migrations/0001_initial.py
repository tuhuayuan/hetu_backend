# Generated by Django 4.2.5 on 2023-10-08 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GrmModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('module_id', models.CharField(max_length=50, unique=True)),
                ('module_secret', models.CharField(max_length=50)),
                ('module_url', models.CharField(max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='NotifyMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_id', models.CharField(db_index=True, max_length=100)),
                ('level', models.CharField(choices=[('default', '默认'), ('info', '信息'), ('warning', '警告'), ('error', '错误'), ('critical', '严重')], max_length=100)),
                ('title', models.CharField(db_index=True, max_length=255)),
                ('content', models.TextField()),
                ('source', models.CharField(max_length=255)),
                ('notified_at', models.DateTimeField(db_index=True)),
                ('created_at', models.DateTimeField()),
                ('ack', models.BooleanField(default=False)),
                ('ack_at', models.DateTimeField(null=True)),
                ('meta', models.JSONField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GrmModuleVar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(max_length=50)),
                ('rw', models.BooleanField(default=False)),
                ('local', models.BooleanField(default=False)),
                ('details', models.CharField(default='', max_length=200)),
                ('module', models.ForeignKey(db_column='module_id', on_delete=django.db.models.deletion.CASCADE, related_name='vars', to='scada.grmmodule', to_field='module_id')),
            ],
            options={
                'unique_together': {('name', 'module')},
            },
        ),
    ]