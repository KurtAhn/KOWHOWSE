import sys
import inspect
import re
from random import randint
from django.db.models import signals
from django.dispatch import receiver
from .definition import *
from .instantiation import *


for n, c in inspect.getmembers(
    sys.modules[__name__],
    lambda o: inspect.isclass(o)
):
    # Set Survey UID
    if c.__name__ == 'Survey':
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

    elif re.match(r'^(Section|End)$', c.__name__):
        def signal(sender, instance, *args, **kwargs):
            instance.species = sender.__name__
            if instance.dummy is None:
                instance.dummy = sender.__name__ == 'End'

    elif re.match(r'^(\w+Question|(Section|End)Feed)$', c.__name__):
        def signal(sender, instance, *args, **kwargs):
            instance.species = sender.__name__

    elif re.match(r'^(\w+Feed)$', c.__name__):
        def signal(sender, instance, *args, **kwargs):
            instance.species = sender.__name__
            if instance.seed is None:
                instance.seed = randint(-sys.maxsize -1, sys.maxsize)

    else:
        continue

    receiver(signals.pre_save, sender=c, weak=False)(signal)
