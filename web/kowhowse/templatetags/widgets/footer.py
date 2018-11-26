from .utils import *


@register.inclusion_tag('footer.html')
def footer(height):
    return {'height': height}
