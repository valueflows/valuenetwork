from django.apps import AppConfig

class WorkAppConfig(AppConfig):
    name = 'work'
    verbose_name = 'Work'

    def ready(self):
        import work.signals
