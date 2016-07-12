from functools import update_wrapper

from django.conf.urls import url
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.admin.views.main import ChangeList


class OrderedModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return [
            url(r'^(.+)/move-(up)/$', wrap(self.move_view),
                name='{app}_{model}_order_up'.format(**self._get_model_info())),

            url(r'^(.+)/move-(down)/$', wrap(self.move_view),
                name='{app}_{model}_order_down'.format(**self._get_model_info())),
        ] + super(OrderedModelAdmin, self).get_urls()

    def _get_changelist(self, request):
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)

        cl = ChangeList(request, self.model, list_display,
                        list_display_links, self.list_filter, self.date_hierarchy,
                        self.search_fields, self.list_select_related,
                        self.list_per_page, self.list_max_show_all, self.list_editable,
                        self)

        return cl

    request_query_string = ''

    def changelist_view(self, request, extra_context=None):
        cl = self._get_changelist(request)
        self.request_query_string = cl.get_query_string()
        return super(OrderedModelAdmin, self).changelist_view(request, extra_context)

    def move_view(self, request, object_id, direction):
        qs = self._get_changelist(request).get_queryset(request)

        obj = get_object_or_404(self.model, pk=unquote(object_id))
        obj.move(direction, qs)

        return HttpResponseRedirect('../../%s' % self.request_query_string)

    def move_up_down_links(self, obj):
        model_info = self._get_model_info()
        return render_to_string("ordered_model/admin/order_controls.html", {
            'app_label': model_info['app'],
            'model_name': model_info['model'],
            'module_name': model_info['model'], # for backwards compatibility
            'object_id': obj.pk,
            'urls': {
                'up': reverse("{admin_name}:{app}_{model}_order_up".format(
                    admin_name=self.admin_site.name, **model_info), args=[obj.pk, 'up']),
                'down': reverse("{admin_name}:{app}_{model}_order_down".format(
                    admin_name=self.admin_site.name, **model_info), args=[obj.pk, 'down']),
            },
            'query_string': self.request_query_string
        })
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')

    def _get_model_info(self):
        return {
            'app': self.model._meta.app_label,
            'model': self.model._meta.model_name,
        }


class OrderedTabularInline(admin.TabularInline):

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

    @classmethod
    def get_model_info(cls):
        return dict(app=cls.model._meta.app_label,
                    model=cls.model._meta.model_name)

    @classmethod
    def get_urls(cls, model_admin):
        def wrap(view):
            def wrapper(*args, **kwargs):
                return model_admin.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return [
            url(r'^(.+)/{model}/(.+)/move-(up)/$'.format(**cls.get_model_info()), wrap(cls.move_view),
                name='{app}_{model}_order_up_inline'.format(**cls.get_model_info())),
            url(r'^(.+)/{model}/(.+)/move-(down)/$'.format(**cls.get_model_info()), wrap(cls.move_view),
                name='{app}_{model}_order_down_inline'.format(**cls.get_model_info())),
        ]

    @classmethod
    def get_list_display(cls, request):
        """
        Return a sequence containing the fields to be displayed on the
        changelist.
        """
        return cls.list_display

    @classmethod
    def get_list_display_links(cls, request, list_display):
        """
        Return a sequence containing the fields to be displayed as links
        on the changelist. The list_display parameter is the list of fields
        returned by get_list_display().
        """
        if cls.list_display_links or not list_display:
            return cls.list_display_links
        else:
            # Use only the first item in list_display as link
            return list(list_display)[:1]

    @classmethod
    def _get_changelist(cls, request):
        list_display = cls.get_list_display(request)
        list_display_links = cls.get_list_display_links(request, list_display)

        cl = ChangeList(request, cls.model, list_display,
                        list_display_links, cls.list_filter, cls.date_hierarchy,
                        cls.search_fields, cls.list_select_related,
                        cls.list_per_page, cls.list_max_show_all, cls.list_editable,
                        cls)

        return cl

    request_query_string = ''

    @classmethod
    def changelist_view(cls, request, extra_context=None):
        cl = cls._get_changelist(request)
        cls.request_query_string = cl.get_query_string()
        return super(OrderedTabularInline, cls).changelist_view(request, extra_context)

    @classmethod
    def get_queryset(cls, request):
        """
        Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view.
        """
        qs = cls.model._default_manager.get_queryset()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = cls.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    @classmethod
    def get_ordering(cls, request):
        """
        Hook for specifying field ordering.
        """
        return cls.ordering or ()  # otherwise we might try to *None, which is bad ;)

    @classmethod
    def get_paginator(cls, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return cls.paginator(queryset, per_page, orphans, allow_empty_first_page)

    @classmethod
    def get_search_fields(cls, request):
        """
        Returns a sequence containing the fields to be searched whenever
        somebody submits a search query.
        """
        return cls.search_fields

    @classmethod
    def get_search_results(cls, request, queryset, search_term):
        """
        Returns a tuple containing a queryset to implement the search,
        and a boolean indicating if the results may contain duplicates.
        """
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        search_fields = cls.get_search_fields(request)
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field))
                           for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(cls.opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    @classmethod
    def move_view(cls, request, admin_id, object_id, direction):
        qs = cls._get_changelist(request).get_queryset(request)

        obj = get_object_or_404(cls.model, pk=unquote(object_id))
        obj.move(direction, qs)

        return HttpResponseRedirect('../../../%s' % cls.request_query_string)

    @classmethod
    def get_preserved_filters(cls, request):
        """
        Returns the preserved filters querystring.
        """
        match = request.resolver_match
        if cls.preserve_filters and match:
            opts = cls.model._meta
            current_url = '%s:%s' % (match.app_name, match.url_name)
            changelist_url = 'admin:%s_%s_changelist' % (opts.app_label, opts.model_name)
            if current_url == changelist_url:
                preserved_filters = request.GET.urlencode()
            else:
                preserved_filters = request.GET.get('_changelist_filters')

            if preserved_filters:
                return urlencode({'_changelist_filters': preserved_filters})
        return ''

    def move_up_down_links(self, obj):
        if obj.id:
            order_obj_name = 'obj'
            if obj._get_order_with_respect_to() is not None:
                order_obj_name = obj._get_order_with_respect_to().id
            return render_to_string("ordered_model/admin/order_controls.html", {
                'app_label': self.model._meta.app_label,
                'model_name': self.model._meta.model_name,
                'module_name': self.model._meta.model_name, # backwards compat
                'object_id': obj.id,
                'urls': {
                    'up': reverse("admin:{app}_{model}_order_up_inline".format(
                        admin_name=self.admin_site.name, **self.get_model_info()),
                        args=[order_obj_name, obj.id, 'up']),
                    'down': reverse("admin:{app}_{model}_order_down_inline".format(
                        admin_name=self.admin_site.name, **self.get_model_info()),
                        args=[order_obj_name, obj.id, 'down']),
                },
                'query_string': self.request_query_string
            })
        else:
            return ''
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')
