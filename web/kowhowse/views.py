from django.urls import reverse, re_path


class Site:
    def __init__(self):
        self._urls = []

    @property
    def urls(self):
        return self._urls, self.AP, self.NS

    def register(self, *views):
        for view in views:
            self._urls.append(re_path(view.url, view.create(), name=view.name))
