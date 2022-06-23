# Generated by Django 3.2.12 on 2022-03-30 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cameras', '0003_auto_20220328_1141'),
        ('alerts', '0003_auto_20220319_1012'),
        ('events', '0002_event'),
        ('users', '0019_userprofile_data_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='favorite_alerts',
            field=models.ManyToManyField(blank=True, related_name='favorited_users', to='alerts.Alert'),
        ),
        migrations.AlterField(
            model_name='user',
            name='favorite_camera_medias',
            field=models.ManyToManyField(blank=True, related_name='favorited_users', to='cameras.CameraMedia'),
        ),
        migrations.AlterField(
            model_name='user',
            name='favorite_events',
            field=models.ManyToManyField(blank=True, related_name='favorited_users', to='events.Event'),
        ),
    ]
