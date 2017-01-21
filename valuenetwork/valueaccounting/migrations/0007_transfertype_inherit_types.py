# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('valueaccounting', '0006_facet_clas'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfertype',
            name='inherit_types',
            field=models.BooleanField(default=False, verbose_name='inherit resource types'),
        ),
    ]
