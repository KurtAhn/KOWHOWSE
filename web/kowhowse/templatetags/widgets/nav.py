from .utils import *


@register.inclusion_tag('widgets/pagebutton.html')
def pagebutton(form, direction):
    assert direction in ['prev', 'next']
    return {'form': form,
            'page_direction': direction,
            'arrow_direction': {'prev': 'left', 'next': 'right'}[direction]}


@register.inclusion_tag('front/nav-main.html')
def nav_main(form):
    return {'form': form}
