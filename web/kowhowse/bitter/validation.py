from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_required(response):
    if not response.is_complete:
        raise ValidationError(
            _('You must provide a response before moving onto another question.'),
            code='missing'
        )


def validate_ab(response):
    if not response.feed.samples.filter(id=response.value.id).exists():
        raise ValidationError(
            _('Response value is not one of the provided samples'),
            code='corrupt'
        )


def validate_mos(response):
    for bit in response.feed.bits.all():
        if not bit.scale.levels.filter(id=bit.value.id).exists():
            raise ValidationError(
                _('Response value is not one of the provided options'),
                code='corrupt'
            )


def validate_mushra_above_90(response):
    if not response.bits.filter(value__gt=90).exists():
        raise ValidationError(
            _('At least one sample must be rated 90 or above'),
            code='custom'
        )


def validate_mushra_below_10(response):
    if not response.bits.filter(value__lt=90).exists():
        raise ValidationError(
            _('At least one sample must be rated 10 or below'),
            code='custom'
        )
