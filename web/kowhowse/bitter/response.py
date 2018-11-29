from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .instantiation import *


class Response(models.Model):
    class Meta:
        abstract = True

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)

    @staticmethod
    def cook(feed, ingredient):
        return {
            AbFeed: AbResponse,
            AbxFeed: AbxResponse,
            MosFeed: MosResponse,
            MushraFeed: MushraResponse
        }[feed.__class__].cook(feed, ingredient)


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

    @staticmethod
    def cook(feed, ingredient):
        AbResponse(feed=feed, value=feed[ingredient]).save()


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

    @staticmethod
    def cook(feed, ingredient):
        AbxResponse(feed=feed, value=feed[ingredient]).save()


class MushraResponse(Response):
    feed = models.OneToOneField(
        MushraFeed,
        on_delete=models.CASCADE,
        related_name='response'
    )

    @staticmethod
    def cook(feed, ingredient):
        response = MushraResponse(feed=feed)
        response.save()
        for k, v in ingredient.items():
            bit = MushraResponseBit(
                whole=response,
                sample=feed[int(k)],
                value=int(v)
            )
            bit.save()
            response.bits.add(bit)


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

    @staticmethod
    def cook(feed, ingredient):
        MosResponse(feed=feed, value=feed[int(ingredient)]).save()
