# Generated by Django 2.0.1 on 2018-02-13 07:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lrex_setup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResponseSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question', models.CharField(max_length=200)),
                ('legend', models.TextField(max_length=1024)),
                ('instructions', models.TextField(max_length=1024)),
                ('reponse_type', models.CharField(choices=[('bin', 'Binary')], default='bin', max_length=3)),
            ],
        ),
        migrations.CreateModel(
            name='BinaryResponseSettings',
            fields=[
                ('responsesettings_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lrex_response_settings.ResponseSettings')),
                ('yes', models.CharField(max_length=200)),
                ('no', models.CharField(max_length=200)),
            ],
            bases=('lrex_response_settings.responsesettings',),
        ),
        migrations.AddField(
            model_name='responsesettings',
            name='setup',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='lrex_setup.Setup'),
        ),
    ]