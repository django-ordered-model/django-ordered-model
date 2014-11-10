from functools import update_wrapper

# from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
# from django.utils.html import strip_spaces_between_tags as short
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.contrib.admin.views.main import ChangeList


class OrderedModelAdmin(admin.ModelAdmin):

    def get_model_info(self):
        return dict(app=self.model._meta.app_label,
                    model=self.model._meta.model_name)

    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        return patterns('',
                        url(r'^(.+)/move-(up)/$', wrap(self.move_view),
                            name='{app}_{model}_order_up'.format(**self.get_model_info())),

                        url(r'^(.+)/move-(down)/$', wrap(self.move_view),
                            name='{app}_{model}_order_down'.format(**self.get_model_info())),
                        ) + super(OrderedModelAdmin, self).get_urls()

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
        cl = self._get_changelist(request)
        qs = cl.get_query_set(request)

        obj = get_object_or_404(self.model, pk=unquote(object_id))
        obj.move(direction, qs)

        return HttpResponseRedirect('../../%s' % self.request_query_string)

    def move_up_down_links(self, obj):
        return render_to_string("ordered_model/admin/order_controls.html", {
            'app_label': self.model._meta.app_label,
            'module_name': self.model._meta.model_name,
            'object_id': obj.id,
            'urls': {
                'up': reverse("admin:{app}_{model}_order_up".format(**self.get_model_info()), args=[obj.id, 'up']),
                'down': reverse("admin:{app}_{model}_order_down".format(**self.get_model_info()), args=[obj.id, 'down']),
            },
            'query_string': self.request_query_string
        })
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')
