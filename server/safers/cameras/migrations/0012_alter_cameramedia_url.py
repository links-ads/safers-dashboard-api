# Generated by Django 3.2.13 on 2022-05-31 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cameras', '0011_alter_cameramedia_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cameramedia',
            name='url',
            field=models.URLField(blank=True, max_length=512, null=True),
        ),
    ]
