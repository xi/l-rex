# Generated by Django 2.0.1 on 2018-02-19 07:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_study', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lrex_study.Study')),
            ],
        ),
    ]
