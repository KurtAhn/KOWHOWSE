from .models import *
import random
import sys


class QuestionAllocator:
    def __init__(self):
        self.seed = lambda: random.randint(-sys.maxsize - 1, sys.maxsize)

    def __call__(self, survey, subject):
        with Paginator(survey, subject):
            for section in survey.sections.all():
                feed = section.feeds.create()
                feed.save()

                for question in section.questions.all():
                    cast = question.cast()
                    if question.species == 'AbQuestion':
                        feed = AbFeed(question=cast,
                                      code=random.choice(AbFeed.CODES)[0])
                        feed.save()
                        feed.samples.add(*random.sample(list(cast.samples.all()), 2))
                    elif question.species == 'AbxQuestion':
                        feed = AbxFeed(question=cast,
                                       seed=self.seed())
                        feed.save()
                        feed.samples.add(*random.sample(list(cast.samples.all()), 2))
                    elif question.species == 'MushraQuestion':
                        feed = MushraFeed(question=cast,
                                          code=random.choice(MushraFeed.CODES))
                        feed.save()
                        feed.samples.add(*random.sample(list(cast.samples.all()), cast.num_choices))
                        reference = random.choice(choices)
                        feed.samples.add(*choices, reference)
                    elif question.species == 'MosQuestion':
                        feed = MosFeed(question=cast)
                        feed.sample = random.choice(list(cast.samples.all()))
                    feed.save()


class ResponseValidator:
    def __init__(self):
        pass

    def __call__(self, response):

        return True

question_allocator = QuestionAllocator()
