from django.apps import AppConfig


class SurveyConfig(AppConfig):
    name = 'survey'

    def ready(self):
        # This is where we load QuestionAllocator etc.
        from . import logic
