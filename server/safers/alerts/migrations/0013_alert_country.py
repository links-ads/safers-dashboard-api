# Generated by Django 4.2 on 2023-06-08 12:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_saferssettings_allow_remote_deletion'),
        ('alerts', '0012_alter_alert_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='alert',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.country'),
        ),
    ]
