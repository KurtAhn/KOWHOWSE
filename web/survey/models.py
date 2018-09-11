from django.db import models
from django.dispatch import receiver
from django.db.models import signals
from django.core.files import File
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
import os
from itertools import chain
from random import Random


class Describable(models.Model):
    class Meta:
        abstract = True

    description = models.CharField(max_length=200)

    def __str__(self):
        return str(self.description)


class Instructable(models.Model):
    class Meta:
        abstract = True

    instruction = models.FileField(upload_to='text/')

    def has_instruction(self):
        return self.instruction

    def instruction_content(self):
        with open(self.instruction.path) as f:
            return f.read()

    def instruction_is_html(self):
        return os.path.splitext(self.instruction.path)[1] == '.html'


class Survey(Describable, Instructable):
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def num_sections(self):
        return len(self.sections.all())

    def num_questions(self):
        return sum(len(getattr(section, attribute).all())
                   for section in self.sections.all()
                   for attribute in dir(section) if 'questions' in attribute)

    def num_subjects(self):
        return len(self.subjects.all())

    def num_ongoing(self):
        return self.num_subjects() - self.num_complete()

    def num_complete(self):
        n = 0
        for subject in self.subjects.all():
            if subject.is_complete():
                n += 1
        return n


class Subject(Describable):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    def current_feed(self):
        page = self.pages.get(is_current=True)
        return page.feed

    def flip_next(self):
        current = self.pages.get(is_current=True)
        if current.next_page is not None:
            current.is_current = False
            current.save()
            current.next_page.is_current = True
            current.next_page.save()

    def flip_prev(self):
        current = self.pages.get(is_current=True)
        if current.prev_page is not None:
            current.is_current = False
            current.save()
            current.prev_page.is_current = True
            current.prev_page.save()

    def is_complete(self):
        for page in self.pages.all():
            if not page.is_complete():
                return False
        return True


class System(Describable):
    pass


class Audio(Describable):
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name='audios',
        default=0
    )
    data = models.FileField(upload_to='audio/')

    def data_format(self):
        return 'audio/'+self.data.path.split('.')[-1]


class Section(Describable, Instructable):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    # updated_date = models.DateTimeField(auto_now=True)


class Question(Describable, Instructable):
    # class Meta:
    #     abstract = True

    species = models.CharField(max_length=10)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    # updated_date = models.DateTimeField(auto_now=True)
    samples = models.ManyToManyField(Audio, related_name='%(class)ss')

    def cast(self):
        return {
            'AbQuestion': AbQuestion,
            'AbxQuestion': AbxQuestion,
            'MushraQuestion': MushraQuestion,
            'MosQuestion': MosQuestion
        }[self.species].objects.get(pk=self.id)


class AbQuestion(Question):
    pass

@receiver(signals.pre_save, sender=AbQuestion)
def AbQuestion_species(sender, instance, *args, **kwargs):
    instance.species = 'AbQuestion'


class AbxQuestion(Question):
    pass

@receiver(signals.pre_save, sender=AbxQuestion)
def AbxQuestion_species(sender, instance, *args, **kwargs):
    instance.species = 'AbxQuestion'


class MushraQuestion(Question):
    num_choices = models.IntegerField()

@receiver(signals.pre_save, sender=MushraQuestion)
def MushraQuestion_species(sender, instance, *args, **kwargs):
    instance.species = 'MushraQuestion'


class MosQuestion(Question):
    num_levels = models.IntegerField()

    def clean(self):
        if self.num_levels <= 0:
            raise ValidationError(_('Positive number of levels required'))

@receiver(signals.pre_save, sender=MosQuestion)
def MosQuestion_species(sender, instance, *args, **kwargs):
    instance.species = 'MosQuestion'


class Page(models.Model):
    """
    An unforunate handle object for feed-like objects.
    This is what's used to string together questions of different types.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='pages'
    )
    prev_page = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        related_name='prev',
        null=True
    )
    next_page = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        related_name='next',
        null=True
    )
    is_current = models.BooleanField(default=False)

    def is_complete(self):
        return self.feed.is_complete()
        # for attribute in dir(self):
        #     if 'feed' != attribute and 'feed' in attribute:
        #         try:
        #             if not getattr(self, attribute).is_complete():
        #                 return False
        #         except ObjectDoesNotExist:
        #             pass
        # assert False

    def is_effectively_first(self):
        return self.prev_page.feed.species == 'NullFeed'
        # for attribute in dir(self.prev_page):
        #     if 'feed' != attribute and 'feed' in attribute:
        #         try:
        #             if isinstance(getattr(self.prev_page, attribute), NullFeed):
        #                 return True
        #         except ObjectDoesNotExist:
        #             pass
        # return False

    def is_effectively_last(self):
        return self.next_page.feed.species == 'NullFeed'
        # return isinstance(self.next_page.feed, NullFeed)


class Feed(models.Model):
    # class Meta:
    #     abstract = True

    species = models.CharField(max_length=10)
    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        related_name='%(class)s',
        null=True
    )

    def cast(self):
        return {
            'SectionFeed': SectionFeed,
            'AbFeed': AbFeed,
            'AbxFeed': AbxFeed,
            'MushraFeed': MushraFeed,
            'MosFeed': MosFeed,
            'NullFeed': NullFeed
        }[self.species].objects.get(pk=self.id)

    def is_complete(self):
        return self.cast().is_complete()
        # raise NotImplementedError('Abstract')


class SectionFeed(Feed):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def is_complete(self):
        return True

@receiver(signals.pre_save, sender=SectionFeed)
def SectionFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'SectionFeed'


class QuestionFeed(Feed):
    class Meta:
        abstract = True

    seed = models.IntegerField(null=True)

    def is_complete(self):
        if hasattr(self, 'response'):
            print(self)
        return hasattr(self, 'response')


class PreferenceFeed(QuestionFeed):
    class Meta:
        abstract = True

    samples = models.ManyToManyField(Audio, related_name='%(class)ss')

    def clean(self):
        for sample in self.samples:
            if sample not in self.question.samples:
                raise ValidationError(_('Invalid sample'))


class AbFeed(PreferenceFeed):
    question = models.ForeignKey(
        AbQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        PreferenceFeed.clean(self)
        if len(self.samples) > 2:
            raise ValidationError(_('There needs to be exactly two systems to compare'))

    def __getitem__(self, key):
        r = Random(self.seed)
        mapping = dict(zip('AB', r.sample(list(self.samples.all()), 2)))
        return mapping[key]

    def choices(self):
        for k in 'AB':
            yield k, self[k]

@receiver(signals.pre_save, sender=AbFeed)
def AbFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'AbFeed'


class AbxFeed(PreferenceFeed):
    question = models.ForeignKey(
        AbxQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        PreferenceFeed.clean(self)
        if len(self.samples) > 2:
            raise ValidationError(_('There needs to be exactly two samples to compare'))

    def __getitem__(self, key):
        r = Random(self.seed)
        mapping = dict(zip('AB', r.sample(list(self.samples.all()), 2)))
        mapping = {**mapping, 'X': r.choice(list(self.samples.all()))}
        return mapping[key]

    def choices(self):
        for k in 'AB':
            yield k, self[k]

@receiver(signals.pre_save, sender=AbxFeed)
def AbxFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'AbxFeed'


class MushraFeed(PreferenceFeed):
    question = models.ForeignKey(
        MushraQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        PreferenceFeed.clean(self)
        if len(self.samples) > self.question.num_choices:
            raise ValidationError(_('Exceeded allowed number of choices'))
        elif len(self.samples) == self.question.num_choices:
            if not (0 <= self.reference() < self.num_choices):
                raise ValidationError(_('Invalid reference'))

    def __getitem__(self, key):
        r = Random(self.seed)
        mapping = dict(zip('AB', r.sample(list(self.samples.all()), 2)))
        mapping = {**mapping, 'X': r.choice(list(self.samples.all()))}
        return mapping[key]

    def choices(self):
        for k in range(self.question.num_choices):
            yield k, self[k]

@receiver(signals.pre_save, sender=MushraFeed)
def MushraFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'MushraFeed'


class MosFeed(QuestionFeed):
    question = models.ForeignKey(
        MosQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )
    sample = models.ForeignKey(Audio, on_delete=models.CASCADE, related_name='mos_feeds')

    def clean(self):
        if self.sample not in self.question.samples:
            raise ValidationError(_('Invalid sample'))

@receiver(signals.pre_save, sender=MosFeed)
def MosFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'MosFeed'


class NullFeed(Feed):
    def is_complete(self):
        return True

@receiver(signals.pre_save, sender=NullFeed)
def NullFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'NullFeed'


class Paginator:
    feed_classes = [SectionFeed, AbFeed, AbxFeed, MushraFeed, MosFeed, NullFeed]

    def __init__(self, survey, subject):
        self._survey = survey
        self._subject = subject
        self._current = None

    def __enter__(self):
        def create_page(sender, instance, *args, **kwargs):
            if instance.page is None:
                page = Page(survey=self._survey, subject=self._subject)
                page.save()
                if self._current is not None:
                    self._current.next_page = page
                    self._current.save()
                    page.prev_page = self._current
                    page.save()
                else:
                    page.is_current = True
                    page.save()
                self._current = page
                instance.page = page

        for c in Paginator.feed_classes:
            signals.pre_save.connect(
                create_page,
                sender=c,
                weak=False,
                dispatch_uid='create_page_{}'.format(c.__name__)
            )
        NullFeed().save()

    def __exit__(self, exc_type, exc_value, exc_tb):
        NullFeed().save()
        for c in Paginator.feed_classes:
            signals.pre_save.disconnect(
                sender=c,
                dispatch_uid='create_page_{}'.format(c.__name__)
            )


class Response(models.Model):
    class Meta:
        abstract = True

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)


class AbResponse(Response):
    feed = models.OneToOneField(
        AbFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.ForeignKey(
        Audio,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    def clean(self):
        if value not in self.feed.samples:
            raise ValidationError(_('Response value is not one of the options'))


class AbxResponse(Response):
    feed = models.OneToOneField(
        AbxFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.ForeignKey(Audio, on_delete=models.CASCADE, related_name='%(class)ss')

    def clean(self):
        if value not in self.feed.samples[:2]:
            raise ValidationError(_('Response value is not one of the options'))


class MushraResponse(Response):
    feed = models.OneToOneField(
        MushraFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )


class MushraResponseBit(models.Model):
    whole = models.ForeignKey(
        MushraResponse,
        on_delete=models.CASCADE,
        related_name='bits'
    )
    sample = models.ForeignKey(
        Audio,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    value = models.IntegerField()

    def clean(self):
        if not (0 <= self.value <= 100):
            raise ValidationError(_('Response value out of range'))


class MosResponse(Response):
    feed = models.OneToOneField(
        MosFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.IntegerField()

    def clean(self):
        if not (0 <= self.value < self.question.num_levels):
            raise ValidationError(_('Response value is not one of the options'))
