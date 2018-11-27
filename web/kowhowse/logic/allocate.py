import random
from ..bitter import *
from .paginate import Paginator


def allocate(survey, subject):
    with Paginator(survey, subject):
        for section in survey.sections.all():
            section.feeds.create().save()

            for question in section.questions.all():
                {   'AbQuestion': create_abfeed,
                    'AbxQuestion': create_abxfeed,
                    'MosQuestion': create_mosfeed,
                    'MushraQuestion': create_mushrafeed
                }[question.species]\
                    (question.cast()) # newline just to fool Atom


def create_abfeed(question):
    feed = AbFeed(question=question)
    feed.save()
    feed.samples.add(*random.sample(list(question.samples.all()), 2))
    feed.save()


def create_abxfeed(question):
    feed = AbxFeed(question=question)
    feed.save()
    feed.samples.add(*random.sample(list(question.samples.all()), 2))
    feed.save()


def create_mosfeed(question):
    feed = MosFeed(question=question)
    feed.sample = random.choice(list(question.samples.all()))
    feed.save()


def create_mushrafeed(question):
    feed = MushraFeed(question=question)
    feed.save()
    feed.samples.add(random.choice(question.references))
    feed.samples.add(
        *random.sample(
            list(question.anchors),
            question.num_anchors or question.anchors.count()
        )
    )
    feed.samples.add(
        *random.sample(
            list(question.stimuli),
            question.num_stimuli or question.stimuli.count()
        )
    )
    feed.save()
