# Generated by Django 2.0.1 on 2018-05-14 13:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lrex_item', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AudioLinkItem',
            fields=[
                ('item_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='lrex_item.Item')),
                ('url', models.URLField(help_text='TODO')),
            ],
            bases=('lrex_item.item',),
        ),
    ]