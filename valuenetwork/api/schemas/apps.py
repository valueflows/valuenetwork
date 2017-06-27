from django.apps import AppConfig
#from django.db.models.signals import post_migrate

#from valuenetwork.api import signals

class ApiSchemasAppConfig(AppConfig):
    name = 'valuenetwork.api.schemas'
    verbose_name = "ApiSchemas"

    def ready(self):
        super(ApiSchemasAppConfig, self).ready()

        #post_migrate.connect(signals.create_notice_types, sender=self)
        
