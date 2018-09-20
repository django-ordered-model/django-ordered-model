import operator

from functools import update_wrapper, reduce

from urllib.parse import urlencode

from django.db import models
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import escape_uri_path, iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib import admin
from django.contrib.admin.utils import unquote, lookup_needs_distinct
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.views.main import ChangeList
from django import VERSION


class BaseOrderedModelAdmin(object):
    """
    Functionality common to both OrderedModelAdmin and OrderedInlineMixin.
    """

    request_query_string = ''

    def _get_model_info(self):
        return {
            'app': self.model._meta.app_label,
            'model': self.model._meta.model_name,
        }

    def _get_changelist(self, request):
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)

        args = (request, self.model, list_display,
                list_display_links, self.list_filter, self.date_hierarchy,
                self.search_fields, self.list_select_related,
                self.list_per_page, self.list_max_show_all, self.list_editable, self)

        if VERSION >= (2, 1):
            args = args + (self.sortable_by, )

        return ChangeList(*args)

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        cl = self._get_changelist(request)
        self.request_query_string = cl.get_query_string()
        return super(BaseOrderedModelAdmin, self).changelist_view(request, extra_context)


class OrderedModelAdmin(BaseOrderedModelAdmin, admin.ModelAdmin):
    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        model_info = self._get_model_info()

        return [
            path('<path:object_id>/move-<direction>/', wrap(self.move_view),
                 name='{app}_{model}_change_order'.format(**model_info)),
        ] + super(OrderedModelAdmin, self).get_urls()

    def move_view(self, request, object_id, direction):
        qs = self._get_changelist(request).get_queryset(request)

        obj = get_object_or_404(self.model, pk=unquote(object_id))

        if direction == 'up':
            obj.up()
        else:
            obj.down()

        # guts from request.get_full_path(), calculating ../../ and restoring GET arguments
        mangled = '/'.join(escape_uri_path(request.path).split('/')[0:-3])
        redir_path = '%s%s%s' % (mangled, '/' if not mangled.endswith('/') else '',
            ('?' + iri_to_uri(request.META.get('QUERY_STRING', ''))) if request.META.get('QUERY_STRING', '') else '')

        return HttpResponseRedirect(redir_path)

    def move_up_down_links(self, obj):
        model_info = self._get_model_info()
        return render_to_string("ordered_model/admin/order_controls.html", {
            'app_label': model_info['app'],
            'model_name': model_info['model'],
            'module_name': model_info['model'], # for backwards compatibility
            'object_id': obj.pk,
            'urls': {
                'up': reverse(
                    "{admin_name}:{app}_{model}_change_order".format(
                        admin_name=self.admin_site.name, **model_info
                    ),
                    args=[obj.pk, 'up']
                ),
                'down': reverse(
                    "{admin_name}:{app}_{model}_change_order".format(
                        admin_name=self.admin_site.name, **model_info
                    ),
                    args=[obj.pk, 'down']
                ),
            },
            'query_string': self.request_query_string
        })
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _('Move')


class OrderedInlineModelAdminMixin(object):
    """
    ModelAdminMixin for classes that contain OrderedInilines
    """

    def get_urls(self):
        urls = super(OrderedInlineModelAdminMixin, self).get_urls()
        for inline in self.inlines:
            if issubclass(inline, OrderedInlineMixin):
                urls = inline(self, self.admin_site).get_urls() + urls
        return urls


class OrderedInlineMixin(BaseOrderedModelAdmin):

    ordering = None
    list_display = ('__str__',)
    list_display_links = ()
    list_filter = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    search_fields = ()
    date_hierarchy = None
    paginator = Paginator
    preserve_filters = True

    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        model_info = self._get_model_info()
        return [
            path(
                '<path:admin_id>/{model}/<path:object_id>/move-<direction>/'.format(**model_info),
                wrap(self.move_view),
                name='{app}_{model}_change_order_inline'.format(**model_info)
            ),
        ]

    def get_list_display(self, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        return self.list_display

    def get_list_display_links(self, request, list_display):
        """
        Return a sequence containing the fields to be displayed as links
        on the changelist. The list_display parameter is the list of fields
        returned by get_list_display().
        """
        if self.list_display_links or not list_display:
            return self.list_display_links
        else:
            # Use only the first item in list_display as link
            return list(list_display)[:1]

    def get_queryset(self, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = self.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def get_ordering(self, request):
        """
        Hook for specifying field ordering.
        """
        return self.ordering or ()  # otherwise we might try to *None, which is bad ;)

    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def get_search_fields(self, request):
        """
        Returns a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return self.search_fields

    def get_search_results(self, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "{0!s}__istartswith".format(field_name[1:])
            elif field_name.startswith('='):
                return "{0!s}__iexact".format(field_name[1:])
            elif field_name.startswith('@'):
                return "{0!s}__search".format(field_name[1:])
            else:
                return "{0!s}__icontains".format(field_name)

        use_distinct = False
        search_fields = self.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(self.opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    def move_view(self, request, admin_id, object_id, direction):
        qs = self._get_changelist(request).get_queryset(request)

        obj = get_object_or_404(self.model, pk=unquote(object_id))

        if direction == 'up':
            obj.up()
        else:
            obj.down()

        # guts from request.get_full_path(), calculating ../../ and restoring GET arguments
        mangled = '/'.join(escape_uri_path(request.path).split('/')[0:-4] + ['change'])
        redir_path = '%s%s%s' % (mangled, '/' if not mangled.endswith('/') else '',
            ('?' + iri_to_uri(request.META.get('QUERY_STRING', ''))) if request.META.get('QUERY_STRING', '') else '')

        return HttpResponseRedirect(redir_path)

    def get_preserved_filters(self, request):
        """
        Returns the preserved filters querystring.
        """
        match = request.resolver_match
        if self.preserve_filters and match:
            opts = self.model._meta
            current_url = '{0!s}:{1!s}'.format(match.app_name, match.url_name)
            changelist_url = 'admin:{0!s}_{1!s}_changelist'.format(opts.app_label, opts.model_name)
            if current_url == changelist_url:
                preserved_filters = request.GET.urlencode()
            else:
                preserved_filters = request.GET.get('_changelist_filters')

            if preserved_filters:
                return urlencode({'_changelist_filters': preserved_filters})
        return ''

    def move_up_down_links(self, obj):
        if not obj.id:
            return ''

        # Find the fields which refer to the parent model of this inline, and
        # use one of them if they aren't None.
        order_with_respect_to = obj._get_order_with_respect_to() or []
        parent_model = self.parent_model._meta
        fields = [
            str(value.pk) for field_name, value in order_with_respect_to
            if value.__class__ is self.parent_model and value is not None and value.pk is not None]
        order_obj_name = fields[0] if len(fields) > 0 else None

        model_info = self._get_model_info()
        if order_obj_name:
            return render_to_string("ordered_model/admin/order_controls.html", {
                'app_label': model_info['app'],
                'model_name': model_info['model'],
                'module_name': model_info['model'],  # backwards compat
                'object_id': obj.pk,
                'urls': {
                    'up': reverse(
                        "admin:{app}_{model}_change_order_inline".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[order_obj_name, obj.id, 'up']
                    ),
                    'down': reverse(
                        "admin:{app}_{model}_change_order_inline".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[order_obj_name, obj.id, 'down']
                    ),
                },
                'query_string': self.request_query_string
            })
        return ''
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _('Move')


class OrderedTabularInline(OrderedInlineMixin, admin.TabularInline):
    pass


class OrderedStackedInline(OrderedInlineMixin, admin.StackedInline):
    pass
