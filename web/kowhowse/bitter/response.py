from django.db import models
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
    value = models.ForeignKey(
        MosLevel,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    @property
    def is_complete(self):
        return self.value is not None

    @staticmethod
    def cook(feed, ingredient):
        if ingredient is not None:
            feed.response.value = feed[int(ingredient)]
        feed.response.clean()
        feed.response.save()
