# Generated by Django 3.2.17 on 2023-02-24 15:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cameras', '0016_alter_camera_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cameramedia',
            old_name='file',
            new_name='media',
        ),       
    ]
