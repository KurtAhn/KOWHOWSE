from django.apps import AppConfig
# from django.contrib.admin.apps import AdminConfig


class KowhowseConfig(AppConfig):
    name = 'kowhowse'

    def ready(self):
        # This is where we load QuestionAllocator etc.
        from . import logic


# class AnalysisConfig(AdminConfig):
#     default_site = 'survey.admin.AnalysisSite'
