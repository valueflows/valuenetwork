from django.apps import AppConfig
import valuenetwork.api.types as types

class ApiTypesAppConfig(AppConfig):
    name = 'valuenetwork.api.types'
    verbose_name = "ApiTypes"

    def ready(self):
        """ Source of this hack:
        https://stackoverflow.com/questions/37862725/django-1-9-how-to-import-in-init-py
        'Adding from .models import CommentMixin imports CommentMixin so that you can use it
        inside the ready() method. It does not magically add it to the comment module so that
        you can access it as comments.CommentMixin
        
        You could assign it to the comments module in the ready() method.'
        from .models import CommentMixin
        comments.CommentMixin = CommentsMixin
        """
        
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

        
