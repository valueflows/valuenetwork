# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0004_auto_20161201_1831'),
        ('work', '0021_ocp_artwork_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ocp_material_type',
            name='facet_value',
        ),
        migrations.RemoveField(
            model_name='ocp_material_type',
            name='material_type',
        ),
        migrations.RemoveField(
            model_name='ocp_material_type',
            name='resource_type',
        ),
        migrations.RemoveField(
            model_name='ocp_nonmaterial_type',
            name='facet_value',
        ),
        migrations.RemoveField(
            model_name='ocp_nonmaterial_type',
            name='nonmaterial_type',
        ),
        migrations.RemoveField(
            model_name='ocp_nonmaterial_type',
            name='resource_type',
        ),
        migrations.DeleteModel(
            name='Ocp_Material_Type',
        ),
        migrations.DeleteModel(
            name='Ocp_Nonmaterial_Type',
        ),
    ]
