# Generated by Django 4.2 on 2023-05-30 13:31

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0011_auto_20220929_1156'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='target_organizations',
        ),
        migrations.AddField(
            model_name='notification',
            name='target_organization_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=64), blank=True, default=list, size=None),
        ),
    ]
