# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0006_auto_20170319_1956'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address_type',
            old_name='space_type',
            new_name='addrTypeSpace_type',
        ),
        migrations.RenameField(
            model_name='company_type',
            old_name='being_type',
            new_name='companyType_being_type',
        ),
        migrations.RenameField(
            model_name='material_type',
            old_name='artwork_type',
            new_name='materialType_artwork_type',
        ),
        migrations.RenameField(
            model_name='nonmaterial_type',
            old_name='artwork_type',
            new_name='nonmaterialType_artwork_type',
        ),
        migrations.RenameField(
            model_name='project_type',
            old_name='being_type',
            new_name='projectType_being_type',
        ),
        migrations.RenameField(
            model_name='record_type',
            old_name='artwork_type',
            new_name='recordType_artwork_type',
        ),
        migrations.RenameField(
            model_name='region_type',
            old_name='space_type',
            new_name='regionType_space_type',
        ),
        migrations.RenameField(
            model_name='unit_type',
            old_name='artwork_type',
            new_name='unitType_artwork_type',
        ),
    ]
