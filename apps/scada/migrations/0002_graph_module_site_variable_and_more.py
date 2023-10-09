# Generated by Django 4.2.5 on 2023-10-09 00:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scada', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Graph',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('status', models.IntegerField()),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('data', models.TextField()),
                ('remark', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated_at', models.DateTimeField(auto_created=True, auto_now=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('module_number', models.CharField(max_length=255, unique=True)),
                ('module_secret', models.CharField(max_length=255)),
                ('module_url', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('contact', models.CharField(max_length=255)),
                ('mobile', models.CharField(max_length=255)),
                ('status', models.IntegerField(default=1)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('remark', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('type', models.CharField(max_length=255)),
                ('rw', models.BooleanField(default=False)),
                ('local', models.BooleanField(default=False)),
                ('details', models.CharField(default='', max_length=255)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='scada.module')),
            ],
            options={
                'unique_together': {('name', 'module')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='grmmodulevar',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='grmmodulevar',
            name='module',
        ),
        migrations.AlterField(
            model_name='notifymessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='notifymessage',
            name='external_id',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='notifymessage',
            name='level',
            field=models.CharField(choices=[('default', '默认'), ('info', '信息'), ('warning', '警告'), ('error', '错误'), ('critical', '严重')], max_length=255),
        ),
        migrations.DeleteModel(
            name='GrmModule',
        ),
        migrations.DeleteModel(
            name='GrmModuleVar',
        ),
    ]