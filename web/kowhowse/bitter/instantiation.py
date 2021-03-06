from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from random import Random
from .definition import *


class Subject(Describable):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    @property
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

    @property
    def is_complete(self):
        for page in self.pages.all():
            if not page.is_complete:
                return False
        return True


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

    @property
    def is_complete(self):
        return self.feed.is_complete

    # FIXME No longer using NullFeed
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
            'EndFeed': EndFeed
        }[self.species].objects.get(pk=self.id)

    @property
    def is_complete(self):
        return self.cast().is_complete


class SectionFeed(Feed):
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    @property
    def is_complete(self):
        return True


class QuestionFeed(Feed):
    class Meta:
        abstract = True

    seed = models.IntegerField()

    @property
    def is_complete(self):
        return self.response.is_complete
        # return hasattr(self, 'response')


class PreferenceFeed(QuestionFeed):
    class Meta:
        abstract = True

    samples = models.ManyToManyField(Audio, related_name='%(class)ss')

    def clean(self):
        for sample in self.samples:
            if sample not in self.question.samples:
                raise ValidationError(
                    _('%(sample)s is an invalid sample'),
                    code='corrupt',
                    param={
                        'sample': sample
                    }
                )
        super().clean()


class AbFeed(PreferenceFeed):
    question = models.ForeignKey(
        AbQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        if self.samples.count() != 2:
            raise ValidationError(
                _('There needs to be exactly two systems to compare'),
                code='corrupt'
            )
        super().clean()

    def __getitem__(self, key):
        if not hasattr(self, '_mapping'):
            r = Random(self.seed)
            self._mapping = dict(
                zip('AB', r.sample(list(self.samples.all()), 2)))
        return self._mapping[key]

    def choices(self):
        for k in 'AB':
            yield k, self[k]


class AbxFeed(PreferenceFeed):
    question = models.ForeignKey(
        AbxQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )

    def clean(self):
        if self.samples.count() != 2:
            raise ValidationError(
                _('There needs to be exactly two samples to compare')
            )
        super().clean()

    def __getitem__(self, key):
        r = Random(self.seed)
        mapping = dict(zip('AB', r.sample(list(self.samples.all()), 2)))
        mapping = {**mapping, 'X': r.choice(list(self.samples.all()))}
        return mapping[key]

    def choices(self):
        for k in 'AB':
            yield k, self[k]


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


class MosFeed(QuestionFeed):
    # Add option for randomizing order
    question = models.ForeignKey(
        MosQuestion,
        on_delete=models.CASCADE,
        related_name='feeds'
    )
    sample = models.ForeignKey(
        Audio, on_delete=models.CASCADE, related_name='mos_feeds'
    )

    def clean(self):
        if self.sample not in self.question.samples:
            raise ValidationError(_('Invalid sample'))

    def __getitem__(self, key):
        if not hasattr(self, '_mapping'):
            self._mapping = list(
                self.question.scales.order_by('-id')
            )
        return self._mapping[key]

    def scales(self):
        for k in range(self.question.scales.all().count()):
            yield self[k]


class EndFeed(Feed):
    @property
    def is_complete(self):
        return True
