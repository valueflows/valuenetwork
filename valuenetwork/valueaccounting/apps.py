from django.apps import AppConfig
from django.db.models.signals import post_migrate

from valuenetwork.valueaccounting import signals

class ValueAccountingAppConfig(AppConfig):
    name = 'valuenetwork.valueaccounting'
    verbose_name = "Value Accounting"

    def ready(self):
        super(ValueAccountingAppConfig, self).ready()

        post_migrate.connect(signals.create_notice_types, sender=self)
        
