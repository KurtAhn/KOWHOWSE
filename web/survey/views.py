from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from .logic import *


def index(request):
    surveys = Survey.objects.order_by('created_date')
    return render(request, 'survey/index.html', {'surveys': surveys})


def survey(request, survey_id):
    survey = get_object_or_404(Survey, pk=survey_id)
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.survey = survey
            subject.save()
            question_allocator(survey, subject)
            subject.flip_next()
            request.session['subject_id'] = subject.id
            return redirect('question', survey_id=survey_id)
    else:
        form = SubjectForm()
    return render(request, 'survey/survey.html', {'survey': survey, 'form': form})


def question(request, survey_id):
    subject = get_object_or_404(Subject, pk=request.session.get('subject_id', None))
    if request.method == "POST":
        print(request.POST)
        direction = request.POST.get('direction', [])
        if direction == 'next':
            subject.flip_next()
        elif direction == 'prev':
            subject.flip_prev()

    feed = subject.current_feed()
    if feed is not None:
        try:
            template, species = {
                'SectionFeed': ('survey/section.html', SectionFeed),
                'AbFeed': ('survey/abquestion.html', AbFeed),
                'AbxFeed': ('survey/abxquestion.html', AbxFeed),
                'MushraFeed': ('survey/mushraquestion.html', MushraFeed),
                'MosFeed': ('survey/mosquestion.html', MosFeed),
                # 'NullFeed': ('survey/null.html', NullFeed)
            }[feed.species]
            return render(request, template, {'feed': species.objects.get(pk=feed.id)})
        except KeyError:
            return HttpResponse('Done')
    else:
        # Finished the survey
        pass
