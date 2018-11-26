from django.utils.safestring import mark_safe
from collections import namedtuple


class Header(namedtuple('Header', 'name content order orderable weight adjust tooltip')):
    __slots__ = ()

    def __str__(self):
        return mark_safe(
            '<th width="{w:.5f}" {a} {o}>{n}</th>'.format(
                w=self.weight,
                n=self.name,
                a='' if not self.adjust else 'align="{}"'.format(self.adjust),
                o='' if not self.orderable else 'orderable',
                t='' if not self.tooltip else 'data-toggle="{}"'.format(self.tooltip)
            ))

    def fit(self, data):
        return mark_safe(
            '<td {a} {o}>{c}</td>'.format(
                a='' if not self.adjust else 'align="{}"'.format(self.adjust),
                o='' if not self.order else 'data-order="{}"'.format(self.order(data)),
                c=self.content(data)
            ))


class Headers:
    def __init__(self):
        self.headers = []

    def add_column(self, name, content, order=None, orderable=True,
                   weight=1.0, adjust=None, tooltip=None):
        self.headers.append(Header(name, content, order, orderable, weight, adjust, tooltip))

    def __iter__(self):
        weight_sum = sum(h.weight for h in self.headers)

        yield from [Header(h.name, h.content,
                           h.order, h.orderable,
                           h.weight / weight_sum, h.adjust, h.tooltip)
                    for h in self.headers]
