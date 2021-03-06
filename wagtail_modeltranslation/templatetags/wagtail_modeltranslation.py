# coding: utf-8

import re

from django import template
from django.core.urlresolvers import resolve
from django.utils.translation import activate, get_language
from six import iteritems

from modeltranslation import settings as mt_settings


register = template.Library()


# TODO: check templatetag usage

# CHANGE LANGUAGE
@register.simple_tag(takes_context=True)
def change_lang(context, lang=None, *args, **kwargs):
    current_language = get_language()

    if 'request' in context and lang and current_language:
        request = context['request']
        match = resolve(request.path)
        non_prefixed_path = re.sub(current_language + '/', '', request.path, count=1)

        # means that is an wagtail page object
        if match.url_name == 'wagtail_serve':
            path_components = [component for component in non_prefixed_path.split('/') if component]
            page, args, kwargs = request.site.root_page.specific.route(request, path_components)

            activate(lang)
            translated_url = page.url
            activate(current_language)

            return translated_url
        elif match.url_name == 'wagtailsearch_search':
            path_components = [component for component in non_prefixed_path.split('/') if component]

            translated_url = '/' + lang + '/' + path_components[0] + '/'
            if request.GET:
                translated_url += '?'
                for key, value in iteritems(request.GET):
                    translated_url += key + '=' + value
            return translated_url

    return ''


class GetAvailableLanguagesNode(template.Node):
    """Get available languages."""

    def __init__(self, variable):
        self.variable = variable

    def render(self, context):
        """Rendering."""
        context[self.variable] = mt_settings.AVAILABLE_LANGUAGES
        return ''


@register.tag('get_available_languages_wmt')
def do_get_available_languages(unused_parser, token):
    """
    Store a list of available languages in the context.

    Usage::

        {% get_available_languages_wmt as languages %}
        {% for language in languages %}
        ...
        {% endfor %}

    This will just pull the MODELTRANSLATION_LANGUAGES (or LANGUAGES) setting
    from your setting file (or the default settings) and
    put it into the named variable.
    """
    args = token.contents.split()
    if len(args) != 3 or args[1] != 'as':
        raise template.TemplateSyntaxError(
            "'get_available_languages_wmt' requires 'as variable' "
            "(got %r)" % args)
    return GetAvailableLanguagesNode(args[2])
