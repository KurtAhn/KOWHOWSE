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
    url = r'^(?P<survey>\w+)/$'
    create = lambda: never_cache(SurveyView.as_view())
    name = 'survey'
    template_name = FrontSite.AP+'/survey.html'
    form_class = SubjectForm

    def post(self, request, *args, **kwargs):
        self.survey = Survey.objects.get(id=kwargs.pop('survey'))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        subject = form.save(commit=False)
        subject.survey = self.survey
        subject.save()
        question_allocator(subject.survey, subject)
        subject.flip_next()
        self.request.session['subject'] = subject.id
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return 'do/'

    @staticmethod
    def locate(survey):
        return '/survey/{}'.format(survey.id)


class QuestionsView(TemplateView):
    url = r'^(?P<survey>\w+)/do/$'
    create = lambda: never_cache(QuestionsView.as_view())
    name = 'questions'
    template_name = FrontSite.AP+'/questions.html'

    def initialize(self, request, *args, **kwargs):
        self.subject = get_object_or_404(
            Subject,
            pk=self.request.session.get('subject', None)
        )

    def get(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        feed = self.subject.current_feed().cast()
        context['feed'] = feed
        return context


class SaveView(RedirectView):
    url = r'^(?P<survey>\w+)/do/save$'
    create = lambda: never_cache(SaveView.as_view())
    name = 'save'
    pattern_name = 'questions'

    def initialize(self, request, *args, **kwargs):
        self.subject = get_object_or_404(
            Subject,
            pk=self.request.session.get('subject', None)
        )

    def post(self, request, *args, **kwargs):
        self.initialize(request, *args, **kwargs)

        feed_id = self.request.POST.get('feed', None)
        if feed_id is not None:
            feed = Feed.objects.get(id=int(self.request.POST['feed'])).cast()
            if isinstance(feed, MushraFeed):
                feed.cook_response({
                    k.replace('response-',''): v
                    for k, v in self.request.POST.items()
                    if k.startswith('response-')
                })
            else:
                feed.cook_response(self.request.POST['response'])

        flip_direction = self.request.POST.get('page', '')
        if flip_direction == 'next':
            self.subject.flip_next()
        elif flip_direction == 'prev':
            self.subject.flip_prev()
        return super().post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return '/survey/{}/do'.format(kwargs['survey'])


site = FrontSite()
site.register(SurveyView, QuestionsView, SaveView)
