# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('valueaccounting', '0005_auto_20161125_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='facet',
            name='clas',
            field=models.CharField(max_length=20, null=True, verbose_name='clas', blank=True),
        ),
    ]
