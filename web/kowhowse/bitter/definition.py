"""
Classes used to define surveys; correspond to those in sweet.py.
"""
from django.db import models
from django.core.files import File
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
import os
from pickle import dumps, loads


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

    @property
    def instruction_content(self):
        if not hasattr(self, '_content'):
            with open(self.instruction.path) as f:
                self._content = f.read()
        return self._content

    def instruction_is_html(self):
        return os.path.splitext(self.instruction.path)[1] == '.html'


class Survey(Describable, Instructable):
    UID_LENGTH = 4

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    public = models.BooleanField()
    uid = models.CharField(
        validators=[MinLengthValidator(UID_LENGTH)],
        max_length=UID_LENGTH,
        primary_key=True
    )

    @property
    def num_sections(self):
        return self.sections.exclude(dummy=True).count()

    @property
    def num_questions(self):
        return sum(len(getattr(section, attribute).all())
                   for section in self.sections.exclude(dummy=True)
                   for attribute in dir(section) if 'questions' in attribute)

    @property
    def num_subjects(self):
        return self.subjects.count()

    @property
    def num_incomplete(self):
        return len([s for s in self.subjects.all() if not s.is_complete])

    @property
    def num_complete(self):
        return len([s for s in self.subjects.all() if s.is_complete])

    @property
    def url(self):
        return ''


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
        return 'audio/' + self.data.path.split('.')[-1]


class Section(Describable, Instructable):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    dummy = models.BooleanField()


class End(Section):
    class Meta:
        proxy = True

    def clean(self):
        if self.questions.exists():
            raise ValidationError(
                _('End section must not contain questions'),
                code='invalid'
            )


class Question(Describable, Instructable):
    species = models.CharField(max_length=16)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    samples = models.ManyToManyField(Audio, related_name='%(class)ss')
    validators = models.BinaryField()

    def cast(self):
        return {
            'AbQuestion': AbQuestion,
            'AbxQuestion': AbxQuestion,
            'MushraQuestion': MushraQuestion,
            'MosQuestion': MosQuestion
        }[self.species].objects.get(pk=self.id)

    @property
    def restored_validators(self):
        yield from loads(self.validators)


class AbQuestion(Question):
    pass


class AbxQuestion(Question):
    pass


class MushraQuestion(Question):
    # Number of anchors to display per feed; leave as null to display all provided
    num_anchors = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True
    )
    # Number of stimuli (samples excluding anchors and reference) per feed;
    # leave as null to display all
    num_stimuli = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True
    )

    @property
    def references(self):
        return self.samples.filter(role='R')

    @property
    def anchors(self):
        return self.samples.filter(role='A')

    @property
    def stimuli(self):
        return self.samples.filter(role='S')


class MosLevel(Describable):
    value = models.FloatField()
    scale = models.ForeignKey(
        'MosScale',
        on_delete=models.CASCADE,
        related_name='levels'
    )

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


class MosScale(Describable):
    def clean(self):
        if len(self.levels) == 0:
            raise ValidationError(
                _('At least one level required'),
                code='invalid'
            )

    def __getitem__(self, key):
        if not hasattr(self, '_mapping'):
            self._mapping = list(
                self.levels.order_by('value')
            )
        return self._mapping[key]

    def choices(self):
        for k in range(self.levels.all().count()):
            yield self[k]

    @property
    def response_str(self):
        return f'response-{self.id}'


class MosQuestion(Question):
    scales = models.ManyToManyField(
        MosScale,
        related_name='%(class)ss'
    )

    def clean(self):
        if len(self.scales) == 0:
            raise ValidationError(
                _('At least one scale required'),
                code='invalid'
            )
