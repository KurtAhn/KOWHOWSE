from django.template.base import FilterExpression
from django.utils.safestring import mark_safe
from .utils import *


@register.tag
def foldy(parser, token):
    tag, args, kwargs = parse_block_tag(parser, token)

    usage = '{{% {tag} name=<str> [expanded=<bool>] [class=<str>] %}}'\
                '<foldyhead>'\
                '<foldybody>'\
            '{{% -{tag} %}}'.format(tag=tag)

    if 'name' not in kwargs.keys():
       raise template.TemplateSyntaxError("Usage: "+usage)

    nodes = parser.parse(('-'+tag,))
    parser.delete_first_token()
    return FoldyNode(
        nodes,
        name=kwargs['name'],
        expanded=kwargs.get('expanded', FilterExpression("False", parser)),
        klass=kwargs.get('class', FilterExpression("", parser))
    )


@register.tag
def foldyhead(parser, token):
    tag, args, kwargs = parse_block_tag(parser, token)

    usage = '{{% {tag} [class=<str>] %}}'\
                '<content>'\
            '{{% -{tag} %}}'.format(tag=tag)

    nodes = parser.parse(('-'+tag,))
    parser.delete_first_token()
    return FoldyheadNode(
        nodes,
        klass=kwargs.get('class', FilterExpression("", parser))
    )


@register.tag
def foldybody(parser, token):
    tag, args, kwargs = parse_block_tag(parser, token)

    usage = '{{% {tag} [class=<str>] %}}'\
                '<content>'\
            '{{% -{tag} %}}'.format(tag=tag)

    nodes = parser.parse(('-'+tag,))
    parser.delete_first_token()
    return FoldybodyNode(
        nodes,
        klass=kwargs.get('class', FilterExpression("", parser))
    )


class FoldyNode(template.Node):
    def __init__(self, nodes, name, expanded, klass):
        self.nodes = nodes
        self.name = name
        self.expanded = expanded
        self.klass = klass

    def render(self, context):
        name = self.name.resolve(context)
        klass = self.klass.resolve(context) or ""
        try:
            expanded = bool(self.expanded.resolve(context))
        except (ValueError, TypeError):
            expanded = False

        output = '<div class="card {klass}">'
        # print(output)
        for node in self.nodes:
            if isinstance(node, FoldyheadNode):
                output += node.render(context)
            elif isinstance(node, FoldybodyNode):
                output += node.render(context)
        output += '</div>'
        return mark_safe(output.format(
            klass=klass,
            name=name,
            expanded=expanded
        ))


class FoldyheadNode(template.Node):
    def __init__(self, nodes, klass):
        self.nodes = nodes
        self.klass = klass

    def render(self, context):
        klass = self.klass.resolve(context) or ""

        output = '<div id="{{name}}-head" '\
                      'class="card-header {klass}" '\
                      'data-toggle="collapse" '\
                      'data-target="#{{name}}-body" '\
                      'aria-expanded="{{expanded}}">'
        # print(output)
        for node in self.nodes:
            output += node.render(context)
        output += '</div>'
        return mark_safe(output.format(klass=klass))


class FoldybodyNode(template.Node):
    def __init__(self, nodes, klass):
        self.nodes = nodes
        self.klass = klass

    def render(self, context):
        klass = self.klass.resolve(context) or ""

        output = '<div id="{{name}}-body" '\
                      'class="collapse show" '\
                      'aria-labelledby="{{name}}-head">'
        output += '<div class="card-body {klass}">'
        # print(output)
        for node in self.nodes:
            output += node.render(context)
        output += '</div>'*2
        return mark_safe(output.format(klass=klass))
