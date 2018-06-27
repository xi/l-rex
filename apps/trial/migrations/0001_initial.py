# Generated by Django 2.0.6 on 2018-06-27 07:27

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_study', '0001_initial'),
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('item_lists', models.ManyToManyField(to='lrex_item.ItemList')),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Study')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('scale_value', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.ScaleValue')),
            ],
        ),
        migrations.CreateModel(
            name='Trial',
            fields=[
                ('slug', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('id', models.CharField(blank=True, help_text='Provide an identification number/name (as instructed by the experimenter).', max_length=200, null=True, verbose_name='ID')),
                ('rating_proof', models.CharField(blank=True, max_length=8, null=True)),
                ('questionnaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Questionnaire')),
            ],
            options={
                'ordering': ['creation_date'],
            },
        ),
        migrations.CreateModel(
            name='TrialItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_item.Item')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.Trial')),
            ],
            options={
                'ordering': ['number'],
            },
        ),
        migrations.AddField(
            model_name='rating',
            name='trial_item',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lrex_trial.TrialItem'),
        ),
    ]
