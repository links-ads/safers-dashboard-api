# Generated by Django 3.2.13 on 2022-06-28 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data', '0008_datatype_source_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='datatype',
            name='domain',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
    ]
