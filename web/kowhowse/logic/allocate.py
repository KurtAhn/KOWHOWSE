import random
from ..bitter import *
from .paginate import Paginator


class QuestionAllocator:
    def __call__(self, survey, subject):
        with Paginator(survey, subject):
            for section in survey.sections.all():
                feed = section.feeds.create()
                feed.save()

                for question in section.questions.all():
                    cast = question.cast()
                    if question.species == 'AbQuestion':
                        feed = AbFeed(question=cast)
                        feed.save()
                        feed.samples.add(*random.sample(list(cast.samples.all()), 2))
                    elif question.species == 'AbxQuestion':
                        feed = AbxFeed(question=cast)
                        feed.save()
                        feed.samples.add(*random.sample(list(cast.samples.all()), 2))
                    elif question.species == 'MushraQuestion':
                        feed = MushraFeed(question=cast)
                        feed.save()
                        feed.samples.add(random.choice(cast.samples.filter(role='R')))
                        feed.samples.add(
                            *random.sample(
                                list(cast.anchors),
                                cast.num_anchors or cast.anchors.count()
                            )
                        )
                        feed.samples.add(
                            *random.sample(
                                list(cast.stimuli),
                                cast.num_stimuli or cast.stimuli.count()
                            )
                        )
                    elif question.species == 'MosQuestion':
                        feed = MosFeed(question=cast)
                        feed.sample = random.choice(list(cast.samples.all()))
                    feed.save()
