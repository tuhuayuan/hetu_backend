# Generated by Django 4.2.5 on 2023-09-27 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alert', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notifymessage',
            name='external_id',
            field=models.CharField(db_index=True, default='', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='notifymessage',
            name='notified_at',
            field=models.DateTimeField(db_index=True),
        ),
    ]