from django import template


register = template.Library()


@register.filter
def add_attr(element, value):
    """a1=v1&a2=v2...
    """
    return element.as_widget(attrs=dict(pair.split('=') for pair in value.split('&')))


@register.filter
def add_class(element, value):
    return element.as_widget(attrs={'class': value})


@register.filter
def add_style(element, value):
    return element.as_widget(attrs={'style': value})
