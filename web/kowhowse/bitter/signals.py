import sys
import inspect
import re
from random import randint
from pickle import dumps

from django.db.models import signals
from django.dispatch import receiver

from .definition import *
from .instantiation import *
from .response import *
from .validation import *


# Set Survey UID
def signal(sender, instance, *args, **kwargs):
    if instance.uid:
        return

    from random import randrange
    from base64 import b64encode

    generate_uid = lambda: \
        b64encode(
            randrange(64**Survey.UID_LENGTH)\
            .to_bytes(-(-Survey.UID_LENGTH * 6 // 8), byteorder='big')
        )\
        .decode('ascii').replace('+', '-').replace('/', '_')

    uid = generate_uid()
    while Survey.objects.filter(uid=uid).exists():
        uid = generate_uid()
    instance.uid = uid

receiver(signals.pre_save, sender=Survey, weak=False)(signal)


# Set species and dummy boolean for Section & End
for n, c in inspect.getmembers(
    sys.modules[__name__],
    lambda o: inspect.isclass(o) and \
              re.match(r'^(Section|End)$', o.__name__)
):
    def signal(sender, instance, *args, **kwargs):
        instance.species = sender.__name__
        if instance.dummy is None:
            instance.dummy = sender.__name__ == 'End'

    receiver(signals.pre_save, sender=c, weak=False)(signal)


# Set species for Question and Feed subclasses
for n, c in inspect.getmembers(
    sys.modules[__name__],
    lambda o: inspect.isclass(o) and \
              re.match(r'^(\w+Question|\w+Feed)$', o.__name__)
):
    def signal(sender, instance, *args, **kwargs):
        instance.species = sender.__name__

    receiver(signals.pre_save, sender=c, weak=False)(signal)


# Set random seed for QuestionFeed subclasses
for n, c in inspect.getmembers(
    sys.modules[__name__],
    lambda o: inspect.isclass(o) and \
              o in PreferenceFeed.__subclasses__() + [MosFeed]
):
    def signal(sender, instance, *args, **kwargs):
        instance.species = sender.__name__
        if instance.seed is None:
            instance.seed = randint(-sys.maxsize -1, sys.maxsize)

    receiver(signals.pre_save, sender=c, weak=False)(signal)


# Set default response for QuestionFeed subclasses
for n, c in inspect.getmembers(
    sys.modules[__name__],
    lambda o: inspect.isclass(o) and \
              o in PreferenceFeed.__subclasses__() + [MosFeed]
):
    def signal(sender, instance, *args, **kwargs):
        if not hasattr(instance, 'response'):
            getattr(
                sys.modules[__name__],
                sender.__name__.replace('Feed', 'Response')
            )(feed=instance).save()

    receiver(signals.post_save, sender=c, weak=False)(signal)


# Set default validators for Question subclasses
def signal(sender, instance, *args, **kwargs):
    if not instance.validators:
        instance.validators = dumps([validate_required, validate_ab])

receiver(signals.pre_save, sender=AbQuestion, weak=False)(signal)
receiver(signals.pre_save, sender=AbxQuestion, weak=False)(signal)


def signal(sender, instance, *args, **kwargs):
    if not instance.validators:
        instance.validators = dumps([validate_required])

receiver(signals.pre_save, sender=MosQuestion, weak=False)(signal)


def signal(sender, instance, *args, **kwargs):
    if not instance.validators:
        instance.validators = dumps([
            validate_required,
            validate_mushra_below_10,
            validate_mushra_above_90
        ])

receiver(signals.pre_save, sender=MushraQuestion, weak=False)(signal)
