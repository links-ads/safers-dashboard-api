# Generated by Django 4.2 on 2023-05-23 10:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0032_remove_user_active_token_key'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Oauth2User',
        ),
    ]
