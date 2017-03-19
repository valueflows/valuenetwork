# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0004_auto_20161201_1831'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accountbank',
            name='company',
        ),
        migrations.RemoveField(
            model_name='accountbank',
            name='human',
        ),
        migrations.RemoveField(
            model_name='accountbank',
            name='record',
        ),
        migrations.RemoveField(
            model_name='accountbank',
            name='unit',
        ),
        migrations.RemoveField(
            model_name='accountces',
            name='entity',
        ),
        migrations.RemoveField(
            model_name='accountces',
            name='human',
        ),
        migrations.RemoveField(
            model_name='accountces',
            name='record',
        ),
        migrations.RemoveField(
            model_name='accountces',
            name='unit',
        ),
        migrations.RemoveField(
            model_name='accountcrypto',
            name='human',
        ),
        migrations.RemoveField(
            model_name='accountcrypto',
            name='record',
        ),
        migrations.RemoveField(
            model_name='accountcrypto',
            name='unit',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='human',
        ),
        migrations.RemoveField(
            model_name='asset',
            name='material',
        ),
        migrations.DeleteModel(
            name='AccountBank',
        ),
        migrations.DeleteModel(
            name='AccountCes',
        ),
        migrations.DeleteModel(
            name='AccountCrypto',
        ),
        migrations.DeleteModel(
            name='Asset',
        ),
    ]
