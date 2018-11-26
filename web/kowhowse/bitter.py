from django.db import models
from django.dispatch import receiver
from django.db.models import signals
from django.core.files import File
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
import os
from itertools import chain
from random import Random, randint
import sys


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

    def num_incomplete(self):
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
    REFERENCE = 'R'
    ANCHOR = 'A'
    STIMULUS = 'S'
    ROLES = (
        (REFERENCE, 'reference'),
        (ANCHOR, 'anchor'),
        (STIMULUS, 'stimulus')
    )

    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name='audios',
        default=0
    )
    data = models.FileField(upload_to='audio/')
    # Only for Mushra; leave as default for other question types
    role = models.CharField(
        max_length=1,
        choices=ROLES,
        default=STIMULUS
    )

    def data_format(self):
        return 'audio/'+self.data.path.split('.')[-1]


class Section(Describable, Instructable):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='sections'
    )


class Question(Describable, Instructable):
    species = models.CharField(max_length=16)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
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
def AbQuestion_pre(sender, instance, *args, **kwargs):
    instance.species = 'AbQuestion'


class AbxQuestion(Question):
    pass

@receiver(signals.pre_save, sender=AbxQuestion)
def AbxQuestion_pre(sender, instance, *args, **kwargs):
    instance.species = 'AbxQuestion'


class MushraQuestion(Question):
    # Number of anchors to display per feed; leave as null to display all provided
    num_anchors = models.PositiveIntegerField(null=True)
    # Number of stimuli (samples excluding anchors and reference) per feed;
    # leave as null to display all
    num_stimuli = models.PositiveIntegerField(null=True)

    @property
    def references(self):
        return self.samples.filter(role='R')

    @property
    def anchors(self):
        return self.samples.filter(role='A')

    @property
    def stimuli(self):
        return self.samples.filter(role='S')

@receiver(signals.pre_save, sender=MushraQuestion)
def MushraQuestion_pre(sender, instance, *args, **kwargs):
    instance.species = 'MushraQuestion'


class MosLevel(Describable):
    value = models.FloatField()

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return not (self > other)

    def __ge__(self, other):
        return not (self < other)

    def __eq__(self, other):
        return self >= other and self <= other

    def __ne__(self, other):
        return not(self == other)


class MosQuestion(Question):
    levels = models.ManyToManyField(MosLevel, related_name='%(class)ss')

    def clean(self):
        if len(self.levels) == 0:
            raise ValidationError(_('Positive number of levels required'))

@receiver(signals.pre_save, sender=MosQuestion)
def MosQuestion_pre(sender, instance, *args, **kwargs):
    instance.species = 'MosQuestion'


class MosQuestionFactory:
    def __init__(self, levels):
        self.levels = levels

    def __enter__(self):
        def attach_levels(sender, instance, *args, **kwargs):
            instance.levels.add(*self.levels)

        signals.pre_save.connect(
            attach_levels,
            sender=MosQuestion,
            weak=False,
            dispatch_uid='attach_levels'
        )

    def __exit__(self, exc_type, exc_value, exc_tb):
        signals.pre_save.disconnect(
            sender=MosQuestion,
            dispatch_uid='attach_levels'
        )


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

    def is_effectively_first(self):
        return self.prev_page.feed.species == 'NullFeed'

    def is_effectively_last(self):
        return self.next_page.feed.species == 'NullFeed'


class Feed(models.Model):
    species = models.CharField(max_length=16)
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
def SectionFeed_pre(sender, instance, *args, **kwargs):
    instance.species = 'SectionFeed'


class QuestionFeed(Feed):
    class Meta:
        abstract = True

    seed = models.IntegerField(null=True) #Move to PreferenceFeed?

    def is_complete(self):
        return hasattr(self, 'response')

@receiver(signals.pre_save, sender=QuestionFeed)
def QuestionFeed_pre(sender, instance, *args, **kwargs):
    if instance.seed == None:
        instance.seed = randint(-sys.maxsize - 1, sys.maxsize)


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

    def cook_response(self, ingredient):
        self.response = AbResponse(feed=self, value=self[ingredient])
        self.response.save()

@receiver(signals.pre_save, sender=AbFeed)
def AbFeed_pre(sender, instance, *args, **kwargs):
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

    def cook_response(self, ingredient):
        self.response = AbxResponse(feed=self, value=self[ingredient])
        self.response.save()

@receiver(signals.pre_save, sender=AbxFeed)
def AbxFeed_pre(sender, instance, *args, **kwargs):
    instance.species = 'AbxFeed'


class MushraFeed(PreferenceFeed):
    question = models.ForeignKey(
        MushraQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        PreferenceFeed.clean(self)
        if self.samples.filter(role='R').count() == 1:
            raise ValidationError(_('Exactly one reference required'))
        elif self.samples.filter(role='A').count() < 1:
            raise ValidationError(_('At least one anchor required'))

    def __getitem__(self, key):
        if not hasattr(self, '_mapping'):
            r = Random(self.seed)
            m = self.samples.all()
            self._mapping = r.sample(list(m), m.count())
        return self._mapping[key]

    @property
    def reference(self):
        if not hasattr(self, '_reference'):
            self._reference = self.samples.get(role='R')
        return self._reference

    @property
    def anchors(self):
        if not hasattr(self, '_anchors'):
            self._anchors = self.samples.filter(role='A')
        return self._anchors

    @property
    def stimuli(self):
        if not hasattr(self, '_stimuli'):
            self._stimuli = self.samples.filter(role='S')
        return self._stimuli

    def choices(self):
        for k in range(self.samples.all().count()):
            yield k, self[k]

    def cook_response(self, ingredient):
        self.response = MushraResponse(feed=self)
        self.response.save()
        for k, v in ingredient.items():
            bit = MushraResponseBit(
                whole=self.response,
                sample=self[int(k)],
                value=int(v)
            )
            bit.save()
            self.response.bits.add(bit)

@receiver(signals.pre_save, sender=MushraFeed)
def MushraFeed_pre(sender, instance, *args, **kwargs):
    instance.species = 'MushraFeed'


class MosFeed(QuestionFeed):
    # Add option for randomizing order
    question = models.ForeignKey(
        MosQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )
    sample = models.ForeignKey(Audio, on_delete=models.CASCADE, related_name='mos_feeds')

    def clean(self):
        if self.sample not in self.question.samples:
            raise ValidationError(_('Invalid sample'))

    def __getitem__(self, key):
        if not hasattr(self, '_mapping'):
            self._mapping = list(self.question.levels.order_by('value'))
        return self._mapping[key]

    def choices(self):
        for k in range(self.question.levels.all().count()):
            yield k, self[k]

    def cook_response(self, ingredient):
        self.response = MosResponse(
            feed=self,
            value=self[int(ingredient)]
        )
        self.response.save()

@receiver(signals.pre_save, sender=MosFeed)
def MosFeed_pre(sender, instance, *args, **kwargs):
    instance.species = 'MosFeed'


class NullFeed(Feed):
    def is_complete(self):
        return True

@receiver(signals.pre_save, sender=NullFeed)
def NullFeed_species(sender, instance, *args, **kwargs):
    instance.species = 'NullFeed'


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
    value = models.PositiveIntegerField()

    def clean(self):
        if not (self.value <= 100):
            raise ValidationError(_('Response value out of range'))


class MosResponse(Response):
    feed = models.OneToOneField(
        MosFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.ForeignKey(
        MosLevel,
        on_delete=models.CASCADE,
        related_name='responses'
    )
