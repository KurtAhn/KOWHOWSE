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
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
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
            redirect(self.NS + ':index')

        from django.contrib.auth.views import LoginView
        from django.contrib.admin.forms import AdminAuthenticationForm

        return LoginView.as_view(
            authentication_form=AdminAuthenticationForm,
            template_name=self.AP + '/login.html',
            extra_context=dict(
                title=_('Log in'),
                app_path=request.get_full_path(),
                username=request.user.get_username(),
                next=reverse(self.NS + ':index', current_app=self.AP)
            )
        )(request)

    @never_cache
    def logout(self, request):
        from django.contrib.auth.views import LogoutView
        return LogoutView.as_view(
            template_name=self.AP + '/logged_out.html',
            extra_context=dict(
                has_permission=False
            )
        )(request)


class IndexView(TemplateView):
    url = r'^$'

    def create(): return login_required(IndexView.as_view())
    name = 'index'
    template_name = BackSite.AP + '/index.html'

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
            dict(
                name=_('Survey Name'),
                content=str,
                weight=5.0
            ),
            dict(
                name=_('Date Created'),
                content=lambda s: s.created_date.strftime('%b %d, %Y at %I:%M:%S %p'),
                order=lambda s: s.created_date.timestamp(),
                weight=5.0
            ),
            dict(
                name=_('Date Updated'),
                content=lambda s: s.updated_date.strftime('%b %d, %Y at %I:%M:%S %p'),
                order=lambda s: s.updated_date.timestamp(),
                weight=5.0
            ),
            dict(
                name=_('Sections'),
                content=lambda s: s.num_sections,
                adjust='center'
            ),
            dict(
                name=_('Questions'),
                content=lambda s: s.num_questions,
                adjust='center'
            ),
            dict(
                name=_('Total Responses'),
                content=lambda s: s.num_subjects,
                adjust='center'
            ),
            dict(
                name=_('Complete Responses'),
                content=lambda s: s.num_complete,
                adjust='center'
            ),
            dict(
                name=_('Incomplete Responses'),
                content=lambda s: s.num_incomplete,
                adjust='center'
            ),
            dict(
                name=_('Actions'),
                content=lambda s: self._actions([
                    # (AnalysisView.locate(s), _('<i>Analyze</i>')),
                    (AnalysisView.locate(s), "<span class='fa fa-eye'/>"),
                    (front.SurveyView.locate(s), "<span class='fa fa-edit'/>"),
                    (spreadsheet_url(s), "<span class='fa fa-download'/>")
                ]),
                adjust='center',
                orderable=False
            )
        ]:
            self._headers.add_column(**h)
        return self._headers

    @property
    def surveys(self):
        return Survey.objects.all()


class AnalysisView(TemplateView):
    url = fr'^analyze/(?P<survey>[\w\-]{{{Survey.UID_LENGTH}}})/$'

    def create(): return login_required(AnalysisView.as_view())
    name = 'analysis'
    template_name = BackSite.AP + '/analysis.html'

    def initialize(self, request, *args, **kwargs):
        self.survey = get_object_or_404(
            Survey,
            pk=kwargs['survey']
        )

    def get(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Respondents:
        # { 'id',
        #   'description',
        #   'start_date',
        #   'end_date',
        #   'complete'
        # }
        # Responses:
        # { 'species',
        #   'id',
        #   'value' (Make sure it's legible),
        #   'start_date',
        #   'end_date',
        #   'respondent'
        # }

        def response_to_dict(r):
            return {
                'species': r.feed.species.replace('Feed', '').lower(),
                'id': r.id,
                # value in terms of accuracy
                'respondent': r.feed.page.subject.id
            }

        kwargs['responses'] = json.dumps(
            [response_to_dict(p)
             for p in self.survey.pages.exclude(feed__species='SectionFeed')],
            cls=DjangoJSONEncoder
        )
        # kwargs['responses'] = json.dumps(
        #     [model_to_dict(p.feed.cast().response)
        #      for p in self.survey.pages.exclude(feed__species='SectionFeed')
        #      ],
        #     cls=DjangoJSONEncoder
        # )
    #    kwargs['respondents'] = json.dumps()
        return super().get_context_data(**kwargs)

    @staticmethod
    def locate(survey):
        return f'analyze/{survey.uid}'


def spreadsheet_url(survey):
    return ''


site = BackSite()
site.register(IndexView, AnalysisView)
