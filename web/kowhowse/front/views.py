from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.edit import FormView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from ..bitter import *
from .forms import *
from ..logic import *
from ..views import Site


class FrontSite(Site):
    AP = 'front'
    NS = 'front'


class SurveyView(FormView):
    url = rf'^(?P<survey>[\w\-]{{{Survey.UID_LENGTH}}})/$'

    @staticmethod
    def create(): return never_cache(SurveyView.as_view())
    name = 'survey'
    template_name = FrontSite.AP + '/survey.html'
    form_class = SubjectForm
    success_url = 'do/'

    def get_context_data(self, **kwargs):
        kwargs['survey'] = get_object_or_404(
            Survey, uid=kwargs.pop('survey')
        )
        return super().get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        self.survey = get_object_or_404(
            Survey, pk=kwargs.pop('survey')
        )
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        subject = form.save(commit=False)
        subject.survey = self.survey
        subject.save()
        question_allocator(subject.survey, subject)
        self.request.session['subject'] = subject.id
        return HttpResponseRedirect(self.get_success_url())

    @staticmethod
    def locate(survey):
        return '/survey/{}'.format(survey.uid)


class QuestionsView(TemplateView):
    url = fr'^(?P<survey>[\w\-]{{{Survey.UID_LENGTH}}})/do/$'

    @staticmethod
    def create(): return never_cache(QuestionsView.as_view())
    name = 'questions'
    template_name = FrontSite.AP + '/questions.html'

    def initialize(self, request, *args, **kwargs):
        self.subject = get_object_or_404(
            Subject,
            pk=self.request.session.get('subject', None)
        )
        self.feed = self.subject.current_feed.cast()

    def get(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)
        ingredient = {
            k.replace('response-', ''): v
            for k, v in self.request.POST.items()
            if k.startswith('response-')
        } if isinstance(self.feed, MushraFeed) \
            else self.request.POST.get('response', None)

        try:
            Response.cook(self.feed, ingredient)
        except ValidationError as e:
            return self.render_to_response(self.get_context_data(**kwargs, error=e))

        flip_direction = self.request.POST.get('page', '')
        if flip_direction == 'next':
            self.subject.flip_next()
        elif flip_direction == 'prev':
            self.subject.flip_prev()
        return redirect('front:questions', survey=kwargs['survey'])

    def get_context_data(self, **kwargs):
        if 'feed' not in kwargs:
            kwargs['feed'] = self.feed
        return super().get_context_data(**kwargs)


site = FrontSite()
site.register(SurveyView, QuestionsView)
