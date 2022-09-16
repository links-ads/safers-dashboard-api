# Generated by Django 3.2.15 on 2022-09-15 15:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='source',
            field=models.CharField(blank=True, choices=[('DSS', 'Decision Support System')], max_length=128, null=True),
        ),
    ]
