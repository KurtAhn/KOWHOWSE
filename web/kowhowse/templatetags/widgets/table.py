from .utils import *


@register.simple_tag
def table_cell(survey, header):
    return header.fit(survey)
