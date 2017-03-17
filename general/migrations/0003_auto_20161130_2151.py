# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0002_auto_20161130_1145'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unitratio',
            name='rate',
            field=models.DecimalField(verbose_name='Ratio multiplier', max_digits=10, decimal_places=4),
        ),
    ]
