from django.utils.translation import gettext as _
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, re_path
from django.template.response import TemplateResponse
from django.contrib import auth
from django.contrib.auth import views
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import TemplateView
import json

from ..views import Site
from ..table import *
from ..bitter import *
from ..front import views as front


class BackSite(Site):
    AP = 'back'
    NS = 'back'

    def __init__(self):
        super().__init__()
        self._urls.extend([
            re_path(r'^login/$', self.login, name='login'),
            re_path(r'^logout/$', self.logout, name='logout')
        ])

    def has_permission(self, request):
        return request.user.is_active and request.user.is_staff

    @never_cache
    def login(self, request):
        if request.method == 'GET' and self.has_permission(request):
            redirect(self.NS+':index')

        from django.contrib.auth.views import LoginView
        from django.contrib.admin.forms import AdminAuthenticationForm

        return LoginView.as_view(
            authentication_form=AdminAuthenticationForm,
            template_name=self.AP+'/login.html',
            extra_context=dict(
                title=_('Log in'),
                app_path=request.get_full_path(),
                username=request.user.get_username(),
                next=reverse(self.NS+':index', current_app=self.AP)
            )
        )(request)

    @never_cache
    def logout(self, request):
        from django.contrib.auth.views import LogoutView
        return LogoutView.as_view(
            template_name=self.AP+'/logged_out.html',
            extra_context=dict(
                has_permission=False
            )
        )(request)


class IndexView(TemplateView):
    url = r'^$'
    create = lambda: login_required(IndexView.as_view())
    name = 'index'
    template_name = BackSite.AP+'/index.html'

    def __init__(self):
        self._headers = None

    def _actions(self, url_content_list):
        return '<div class="d-flex flex-wrap justify-content-center">{}</div>'.format(
            ''.join('<a href="{}" class="badge badge-primary m-1">{}</a>'.format(a, c)
                    for a, c in url_content_list)
        )

    def _action(url, content):
        return '<a href="{}" class="badge badge-primary">{}</a>'.format(url, content)

    @property
    def headers(self):
        if self._headers is not None:
            return self._headers

        self._headers = Headers()
        for h in [
            dict(name='Survey Name', content=str, weight=5.0),
            dict(name='Date Created', content=lambda s: s.created_date.strftime('%b %d, %Y at %I:%M:%S %p'),
                 order=lambda s: s.created_date.timestamp(), weight=5.0),
            dict(name='Date Updated', content=lambda s: s.updated_date.strftime('%b %d, %Y at %I:%M:%S %p'),
                 order=lambda s: s.updated_date.timestamp(), weight=5.0),
            dict(name='S', content=lambda s: s.num_sections, adjust='center',
                 tooltip='Number of Sections'),
            dict(name='Q', content=lambda s: s.num_questions, adjust='center'),
            dict(name='IR', content=lambda s: s.num_incomplete, adjust='center'),
            dict(name='CR', content=lambda s: s.num_complete, adjust='center'),
            dict(name='TR', content=lambda s: s.num_subjects, adjust='center'),
            dict(name='A',
                 content=lambda s: self._actions([
                    (AnalysisView.locate(s), 'Analyze'),
                    (front.SurveyView.locate(s), 'Try It')]),
                 adjust='center', orderable=False)
        ]:
            self._headers.add_column(**h)
        return self._headers

    @property
    def surveys(self):
        return Survey.objects.all()


class AnalysisView(TemplateView):
    url = r'^analyze/$'
    create = lambda: login_required(AnalysisView.as_view())
    name = 'analysis'
    template_name = BackSite.AP+'/analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        responses = [
            page
            for subject in self.survey.subjects.all()
            for page in subject.pages.exclude(
                feed__species__in='SectionFeed NullFeed'.split()
            )
        ]
        # print(responses)

        # context['responses'] = simplejson.dumps(responses)
        return context

    @property
    def survey(self):
        return Survey.objects.get(id=self.request.GET['survey'])

    @staticmethod
    def locate(survey):
        return 'analyze?survey={}'.format(survey.uid)


site = BackSite()
site.register(IndexView, AnalysisView)
