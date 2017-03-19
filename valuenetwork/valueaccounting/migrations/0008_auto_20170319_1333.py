# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('valueaccounting', '0007_transfertype_inherit_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agenttype',
            name='party_type',
            field=models.CharField(default=b'individual', max_length=12, verbose_name='party type', choices=[(b'individual', 'individual'), (b'org', 'organization'), (b'network', 'network'), (b'team', 'project'), (b'community', 'community'), (b'company', 'company')]),
        ),
    ]
