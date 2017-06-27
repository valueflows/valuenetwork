from django.apps import AppConfig
import valuenetwork.api.types as types

class ApiTypesAppConfig(AppConfig):
    name = 'valuenetwork.api.types'
    verbose_name = "ApiTypes"

    def ready(self):
        #import pdb; pdb.set_trace()
        
        from valuenetwork.api.types.EconomicResource import EconomicResource, EconomicResourceCategory
        types.EconomicResource = EconomicResource
        types.EconomicResourceCategory = EconomicResourceCategory
        from valuenetwork.api.types.Agent import Agent
        types.Agent = Agent
        from valuenetwork.api.types.Process import Process
        types.Process = Process
        from valuenetwork.api.types.EconomicEvent import EconomicEvent
        types.EconomicEvent = EconomicEvent
        super(ApiTypesAppConfig, self).ready()

        
