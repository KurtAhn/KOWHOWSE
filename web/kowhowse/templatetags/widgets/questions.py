from .utils import *
from django.utils.translation import gettext_lazy as _
from ...bitter import Instructable


@register.inclusion_tag('back/qtypefilters.html')
def qtypefilters():
    return {'num_mos': 10}


@register.inclusion_tag('front/instruction.html')
def instruction(instructable, error):
    assert isinstance(instructable, Instructable)
    return {'instructable': instructable, 'error': _(error)}


@register.inclusion_tag('front/aboptions.html')
def aboptions(feed):
    return {'feed': feed}


@register.inclusion_tag('front/mosoptions.html')
def mosoptions(feed):
    return {'feed': feed}


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
