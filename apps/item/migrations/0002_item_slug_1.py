# Generated by Django 2.1.1 on 2018-09-24 07:35
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0001_initial'),
        ('lrex_experiment', '0003_update_slugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='slug',
            field=models.SlugField(null=True),
        ),
    ]
