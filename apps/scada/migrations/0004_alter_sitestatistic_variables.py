# Generated by Django 4.2.6 on 2023-11-02 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scada', '0003_sitestatistic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitestatistic',
            name='variables',
            field=models.ManyToManyField(to='scada.variable'),
        ),
    ]