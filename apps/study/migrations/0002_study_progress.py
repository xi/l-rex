# Generated by Django 2.0.1 on 2018-04-11 09:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_study', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='study',
            name='progress',
            field=models.CharField(choices=[('00sc', 'Create a study'), ('01ss', 'Configure scale '), ('02ec', 'Create a new experiment'), ('03ic', 'Create or upload experiment items'), ('04iv', 'Validate the experiment items consistancy'), ('05lc', 'Generate item lists'), ('06sq', 'Generate questionnaires'), ('07sq', 'Run a study')], default='00sc', max_length=4),
        ),
    ]