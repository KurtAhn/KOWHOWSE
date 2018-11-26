from .utils import *


@register.inclusion_tag('widgets/playbutton.html')
def playbutton(audio, _class=''):
    return {'audio': audio, 'class': _class}


@register.inclusion_tag('widgets/volume.html')
def volume():
    return {}


@register.inclusion_tag('widgets/audio.js.html', name='audio.js')
def audio_js(play='fa-play', pause='fa-pause'):
    return {'play': play, 'pause': pause}
