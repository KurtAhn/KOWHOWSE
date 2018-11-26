from .utils import *
from django.utils.safestring import mark_safe


@register.tag
def radio(parser, token):
    tag, args, kwargs = parse_block_tag(parser, token)

    usage = '{{% {tag} name=<str> '\
                      'value=<str> '\
                      '[id=<str>] '\
                      '[required=<bool>]'\
                      '[active=<bool>]'\
                      '[class=<str>] %}}'\
                '<content>'\
            '{{% -{tag} %}}'.format(tag=tag)

    if 'name' not in kwargs.keys() or \
       'value' not in kwargs.keys():
       raise template.TemplateSyntaxError("Usage: "+usage)

    nodes = parser.parse(('-'+tag,))
    parser.delete_first_token()
    return RadioNode(
        nodes,
        name=kwargs['name'],
        value=kwargs['value'],
        idee=kwargs.get('id', FilterExpression("", parser)),
        required=kwargs.get('required', FilterExpression("False", parser)),
        active=kwargs.get('active', FilterExpression("False", parser)),
        klass=kwargs.get('class', FilterExpression("", parser))
    )


class RadioNode(template.Node):
    def __init__(self, nodes, name, value, idee, required, active, klass):
        self.nodes = nodes
        self.name = name
        self.value = value
        self.idee = idee
        self.required = required
        self.active = active
        self.klass = klass

    def render(self, context):
        name = self.name.resolve(context)
        value = self.value.resolve(context)
        idee = self.value.resolve(context)
        if not idee:
            idee = '{}-{}'.format(name, value)

        klass = self.klass.resolve(context)

        try:
            required = bool(self.required.resolve(context))
        except (ValueError, TypeError):
            required = False

        try:
            active = bool(self.active.resolve(context))
        except (ValueError, TypeError):
            active = False

        output = '<label class="btn {active} {klass}">'
        output += '<input type="radio" '\
                         'name="{name}" '\
                         'value="{value}" '\
                         'id="{idee}" '\
                         '{required}>'
        for node in self.nodes:
            output += node.render(context)
        output += '</input></label>'
        output = mark_safe(output.format(
            name=name,
            value=value,
            idee=idee,
            required='required' if required else '',
            active='active' if active else '',
            klass=klass if klass else ""
        ))
        # print(output)
        return output
