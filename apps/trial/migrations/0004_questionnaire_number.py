# Generated by Django 2.1.2 on 2018-11-08 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_trial', '0003_randomize_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionnaire',
            name='number',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
