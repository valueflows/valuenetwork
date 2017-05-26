# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-26 09:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fairpay', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='fairpayoauth2',
            old_name='access_token',
            new_name='access_key',
        ),
        migrations.RenameField(
            model_name='fairpayoauth2',
            old_name='refresh_token',
            new_name='access_secret',
        ),
        migrations.RemoveField(
            model_name='fairpayoauth2',
            name='expires_token',
        ),
        migrations.AddField(
            model_name='fairpayoauth2',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]