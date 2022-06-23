# Generated by Django 3.2.12 on 2022-03-17 10:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0011_user_default_aoi'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='oauth2user',
            options={'verbose_name': 'User Profile (oauth2)', 'verbose_name_plural': 'User Profiles (oauth2)'},
        ),
        migrations.AlterField(
            model_name='oauth2user',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_users', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile (local)',
                'verbose_name_plural': 'User Profiles (local)',
            },
        ),
    ]
