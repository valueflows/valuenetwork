from django.apps import AppConfig
#from django.db.models.signals import post_migrate

from valuenetwork.api import signals

class ApiAppConfig(AppConfig):
    name = 'valuenetwork.api'
    verbose_name = "API"

    def ready(self):
        super(ApiAppConfig, self).ready()

        #post_migrate.connect(signals.create_notice_types, sender=self)
        
