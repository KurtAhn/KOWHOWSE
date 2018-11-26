from django.template.base import FilterExpression, kwarg_re
from django import template


def inclusion_tag(self, filename, func=None, takes_context=None, name=None):
    """
    I made some modification to the default inclusion_tag
    """
    import functools
    from inspect import getfullargspec
    from django.template.library import InclusionNode, parse_bits

    def dec(func):
            params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
            params = [p if not p.startswith('_') else p[1:] for p in params]
            function_name = (name or getattr(func, '_decorated_function', func).__name__)

            @functools.wraps(func)
            def compile_func(parser, token):
                bits = token.split_contents()[1:]
                args, kwargs = parse_bits(
                    parser, bits, params, varargs, varkw, defaults,
                    kwonly, kwonly_defaults, takes_context, function_name,
                )
                if 'class' in kwargs:
                    kwargs['_class'] = kwargs['class']
                    del kwargs['class']
                return InclusionNode(
                    func, takes_context, args, kwargs, filename,
                )
            self.tag(function_name, compile_func)
            return func
    return dec

template.Library.inclusion_tag = inclusion_tag
register = template.Library()


def parse_block_tag(parser, token):
    # Adapted from https://www.caktusgroup.com/blog/2017/05/01/building-custom-block-template-tag/
    bits = token.split_contents()
    tag_name = bits.pop(0)
    args = []
    kwargs = {}
    for bit in bits:
        match = kwarg_re.match(bit)
        kwarg_format = match and match.group(1)
        if kwarg_format:
            key, value = match.groups()
            kwargs[key] = FilterExpression(value, parser)
        else:
            args.append()
    return (tag_name, args, kwargs)
