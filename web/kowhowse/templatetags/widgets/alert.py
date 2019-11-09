from .utils import *


@register.inclusion_tag('widgets/alert.html')
def alert(message='', _class='', dismissible=True):
    return {
        'message': message,
        'class': _class,
        'dismissible': dismissible
    }
