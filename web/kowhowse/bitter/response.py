from django.db import models
from django.db.models.signals import post_init
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .instantiation import *


class Response(models.Model):
    class Meta:
        abstract = True

    # TODO Implement duration tracking
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)

    def clean(self):
        for v in self.feed.question.restored_validators:
            v(self)
        super().clean()

    @staticmethod
    def cook(feed, ingredient):
        try:
            {
                AbFeed: AbResponse,
                AbxFeed: AbxResponse,
                MosFeed: MosResponse,
                MushraFeed: MushraResponse
            }[feed.__class__].cook(feed, ingredient)
        except KeyError:
            pass


class AbResponse(Response):
    feed = models.OneToOneField(
        AbFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.ForeignKey(
        Audio,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        null=True
    )

    @property
    def is_complete(self):
        return self.value is not None

    @staticmethod
    def cook(feed, ingredient):
        if ingredient is not None:
            feed.response.value = feed[ingredient]
        feed.response.clean()
        feed.response.save()


class AbxResponse(Response):
    feed = models.OneToOneField(
        AbxFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )
    value = models.ForeignKey(
        Audio,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        null=True
    )

    @property
    def is_complete(self):
        return self.value is not None

    @staticmethod
    def cook(feed, ingredient):
        if ingredient is not None:
            feed.response.value = feed[ingredient]
        feed.response.clean()
        feed.response.save()


class MushraResponse(Response):
    feed = models.OneToOneField(
        MushraFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )

    @property
    def is_complete(self):
        # FIXME prolly wrong lol
        try:
            self.clean()
            return True
        except ValidationError:
            return False

    @staticmethod
    def cook(feed, ingredient):
        for k, v in ingredient.items():
            bit = feed.response.bits.get(sample_id=int(k))
            bit.value = int(v)
            bit.clean()
            bit.save()
        response.clean()


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
    value = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=50
    )


class MosResponse(Response):
    feed = models.OneToOneField(
        MosFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )

    @property
    def is_complete(self):
        return all(
            bit.is_complete
            for bit in self.bits.all()
        )

    @staticmethod
    def cook(feed, ingredient):
        if ingredient is not None:
            for k, v in ingredient.items():
                bit = feed.response.bits.get(scale_id=int(k))
                bit.value = MosLevel.objects.get(id=int(v))
                bit.clean()
                bit.save()
        feed.response.clean()
        feed.response.save()


# Populate MosResponse with MosResponseBit obejcts
def populate_mosresponse(**kwargs):
    instance = kwargs.get('instance')
    instance.save()
    if not instance.bits.exists():
        for scale in instance.feed.question.scales.order_by('id'):
            MosResponseBit(
                whole=instance,
                scale=scale
            ).save()
    
post_init.connect(populate_mosresponse, MosResponse)


class MosResponseBit(models.Model):
    whole = models.ForeignKey(
        MosResponse,
        on_delete=models.CASCADE,
        related_name='bits'
    )
    scale = models.ForeignKey(
        MosScale,
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    value = models.ForeignKey(
        MosLevel,
        on_delete=models.CASCADE,
        related_name='responses',
        null=True
    )

    @property
    def is_complete(self):
        return self.value is not None