# Generated by Django 2.0.1 on 2018-05-29 08:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_experiment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='experiment',
            name='title',
            field=models.CharField(help_text='TODO', max_length=200, unique=True),
        ),
    ]