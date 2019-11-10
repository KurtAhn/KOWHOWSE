from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404
from .utils import *
from ...bitter import *


@register.inclusion_tag('back/qtypefilters.html')
def qtypefilters(survey):
    return {}


@register.inclusion_tag('front/instruction.html')
def instruction(instructable, error):
    assert isinstance(instructable, Instructable)
    return {'instructable': instructable, 'error': _(error)}


@register.inclusion_tag('front/aboption.html')
def aboption(value, response):
    return {'value': value, 'active': value == response}


@register.inclusion_tag('front/aboptions.html')
def aboptions(feed):
    response = feed.response.value if hasattr(feed, 'response') else None
    return dict(
        options=[
            dict(
                value=k,
                active=v == response,
                audio=v
            )
            for k, v in feed.choices()
        ]
    )


@register.inclusion_tag('front/mosscales.html')
def mosscales(feed):
    return dict(
        scales=[
            dict(
                name=f'response-{scale.id}',
                description=scale.description,
                levels=[
                    dict(
                        value=level.id,
                        description=level.description,
                        active=(
                            feed.response.bits.get(scale_id=scale.id).value == level
                            if (
                                hasattr(feed, 'response') and
                                feed.response.bits.exists() and 
                                feed.response.bits.get(scale_id=scale.id).value is not None
                            ) else False
                        )
                    )
                    for level in scale.levels.order_by('value')
                ]
            )
            for scale in feed.question.scales.order_by('id')
        ]
    )


@register.inclusion_tag('front/mushrastimulus.html')
def mushrastimulus(name, audio):
    return {'name': name, 'audio': audio}


@register.inclusion_tag('front/mushrareference.html')
def mushrareference(audio):
    return {'audio': audio}


@register.inclusion_tag('front/mushra.js.html', name='mushra.js')
def mushra_js():
    return {}


@register.inclusion_tag('front/mushra.css.html', name='mushra.css')
def mushra_css(width, height, base='0px'):
    return {'width': width, 'height': height, 'base': base}


@register.inclusion_tag('widgets/help.html')
def help(message):
    return {'message': message}
