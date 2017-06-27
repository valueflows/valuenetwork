from django.apps import AppConfig

class ApiAppConfig(AppConfig):
    name = 'valuenetwork.api'
    verbose_name = "API"

    def ready(self):
        from .types.Agent import Agent
        from .types.EconomicResource import EconomicResource, EconomicResourceCategory
        from .types.Process import Process
        from .types.EconomicEvent import EconomicEvent
        super(ApiAppConfig, self).ready()

        
