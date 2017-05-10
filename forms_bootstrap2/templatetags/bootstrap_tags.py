from django import template
from django.template.loader import get_template
from django import VERSION as DJANGO_VERSION

if DJANGO_VERSION >= (1, 10, 0):
    context_class = dict
else:
    # Django<1.10 compatibility
    from django.template import Context
    context_class = Context

register = template.Library()

@register.filter
def as_bootstrap(form):
    template = get_template("bootstrap/form.html")
    c = context_class({"form": form})
    return template.render(c)


@register.filter
def css_class(field):
    return field.field.widget.__class__.__name__.lower()
