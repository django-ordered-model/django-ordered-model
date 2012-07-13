from django.conf import settings
from django.contrib import admin
from django.contrib.admin.util import unquote
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import update_wrapper
from django.utils.html import strip_spaces_between_tags as short
from django.utils.translation import ugettext_lazy as _

class OrderedModelAdmin(admin.ModelAdmin):
    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)
        info = self.model._meta.app_label, self.model._meta.module_name
        return patterns('',
            url(r'^(.+)/move-(up)/$',
                wrap(self.move_view),
                name='%s_%s_move_up' % info),
            url(r'^(.+)/move-(down)/$',
                wrap(self.move_view),
                name='%s_%s_move_down' % info),
        ) + super(OrderedModelAdmin, self).get_urls()
        
    def move_view(self, request, object_id, direction):
        obj = get_object_or_404(self.model, pk=unquote(object_id))
        if direction == 'up':
            obj.move_up()
        else:
            obj.move_down()
        return HttpResponseRedirect('../../')
    
    link_html = short("""
        <a href="../../%(app_label)s/%(module_name)s/%(object_id)s/move-up/">
            <img src="%(STATIC_URL)sordered_model/arrow-up.gif" alt="Move up" />
        </a>
        <a href="../../%(app_label)s/%(module_name)s/%(object_id)s/move-down/">
            <img src="%(STATIC_URL)sordered_model/arrow-down.gif" alt="Move down" />
        </a>""")
    
    def move_up_down_links(self, obj):
        return self.link_html % {
            'app_label': self.model._meta.app_label,
            'module_name': self.model._meta.module_name,
            'object_id': obj.id,
            'STATIC_URL': settings.STATIC_URL,
        }
    move_up_down_links.allow_tags = True
    move_up_down_links.short_description = _(u'Move')
    
