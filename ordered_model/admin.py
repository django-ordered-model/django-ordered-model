from functools import update_wrapper

from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.encoding import escape_uri_path, iri_to_uri
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string
from django.contrib import admin
from django.contrib.admin.utils import unquote
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.views.main import ChangeList
from django import VERSION


class BaseOrderedModelAdmin:
    """
    Functionality common to both OrderedModelAdmin and OrderedInlineMixin.
    """

    request_query_string = ""

    def _get_model_info(self):
        return {"app": self.model._meta.app_label, "model": self.model._meta.model_name}

    def _get_changelist(self, request):
        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)

        args = (
            request,
            self.model,
            list_display,
            list_display_links,
            self.list_filter,
            self.date_hierarchy,
            self.search_fields,
            self.list_select_related,
            self.list_per_page,
            self.list_max_show_all,
            self.list_editable,
            self,
        )

        if VERSION >= (2, 1):
            args = args + (self.sortable_by,)

        return ChangeList(*args)

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        cl = self._get_changelist(request)
        self.request_query_string = cl.get_query_string()
        return super().changelist_view(request, extra_context)


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
            path(
                "<path:object_id>/move-<direction>/",
                wrap(self.move_view),
                name="{app}_{model}_change_order".format(**model_info),
            )
        ] + super().get_urls()

    def move_view(self, request, object_id, direction):
        obj = get_object_or_404(self.model, pk=unquote(object_id))

        if direction not in ("up", "down", "top", "bottom"):
            raise Http404

        getattr(obj, direction)()

        # guts from request.get_full_path(), calculating ../../ and restoring GET arguments
        mangled = "/".join(escape_uri_path(request.path).split("/")[0:-3])
        redir_path = "%s%s%s" % (
            mangled,
            "/" if not mangled.endswith("/") else "",
            ("?" + iri_to_uri(request.META.get("QUERY_STRING", "")))
            if request.META.get("QUERY_STRING", "")
            else "",
        )

        return HttpResponseRedirect(redir_path)

    def move_up_down_links(self, obj):
        model_info = self._get_model_info()
        return render_to_string(
            "ordered_model/admin/order_controls.html",
            {
                "app_label": model_info["app"],
                "model_name": model_info["model"],
                "module_name": model_info["model"],  # for backwards compatibility
                "object_id": obj.pk,
                "urls": {
                    "up": reverse(
                        "{admin_name}:{app}_{model}_change_order".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[obj.pk, "up"],
                    ),
                    "down": reverse(
                        "{admin_name}:{app}_{model}_change_order".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[obj.pk, "down"],
                    ),
                    "top": reverse(
                        "{admin_name}:{app}_{model}_change_order".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[obj.pk, "top"],
                    ),
                    "bottom": reverse(
                        "{admin_name}:{app}_{model}_change_order".format(
                            admin_name=self.admin_site.name, **model_info
                        ),
                        args=[obj.pk, "bottom"],
                    ),
                },
                "query_string": self.request_query_string,
            },
        )

    move_up_down_links.short_description = _("Move")


class OrderedInlineModelAdminMixin:
    """
    ModelAdminMixin for classes that contain OrderedInilines
    """

    def get_urls(self):
        urls = super().get_urls()
        for inline in self.inlines:
            if issubclass(inline, OrderedInlineMixin):
                urls = inline(self.model, self.admin_site).get_urls() + urls
        return urls


class OrderedInlineMixin(BaseOrderedModelAdmin):
    def _get_model_info(self):
        return dict(
            **super()._get_model_info(),
            parent_model=self.parent_model._meta.model_name,
        )

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
                "<path:admin_id>/{model}/<path:object_id>/move-<direction>/".format(
                    **model_info
                ),
                wrap(self.move_view),
                name="{app}_{parent_model}_{model}_change_order_inline".format(
                    **model_info
                ),
            )
        ]

    def move_view(self, request, admin_id, object_id, direction):
        obj = get_object_or_404(self.model, pk=unquote(object_id))

        if direction not in ("up", "down", "top", "bottom"):
            raise Http404

        getattr(obj, direction)()

        # guts from request.get_full_path(), calculating ../../ and restoring GET arguments
        mangled = "/".join(escape_uri_path(request.path).split("/")[0:-4] + ["change"])
        redir_path = "%s%s%s" % (
            mangled,
            "/" if not mangled.endswith("/") else "",
            ("?" + iri_to_uri(request.META.get("QUERY_STRING", "")))
            if request.META.get("QUERY_STRING", "")
            else "",
        )

        return HttpResponseRedirect(redir_path)

    def move_up_down_links(self, obj):
        if not obj.pk:
            return ""

        # Find the fields which refer to the parent model of this inline, and
        # use one of them if they aren't None.
        order_with_respect_to = (
            obj._meta.default_manager._get_order_with_respect_to_filter_kwargs(obj)
            or []
        )

        fields = [
            str(value.pk)
            for value in order_with_respect_to.values()
            if (
                type(value) == self.parent_model
                or issubclass(self.parent_model, type(value))
            )
            and value is not None
            and value.pk is not None
        ]
        order_obj_name = fields[0] if len(fields) > 0 else None

        model_info = self._get_model_info()
        if not order_obj_name:
            return ""

        name = "{admin_name}:{app}_{parent_model}_{model}_change_order_inline".format(
            admin_name=self.admin_site.name, **model_info
        )

        return render_to_string(
            "ordered_model/admin/order_controls.html",
            {
                "app_label": model_info["app"],
                "model_name": model_info["model"],
                "module_name": model_info["model"],  # backwards compat
                "object_id": obj.pk,
                "urls": {
                    "up": reverse(name, args=[order_obj_name, obj.pk, "up"]),
                    "down": reverse(name, args=[order_obj_name, obj.pk, "down"]),
                    "top": reverse(name, args=[order_obj_name, obj.pk, "top"]),
                    "bottom": reverse(name, args=[order_obj_name, obj.pk, "bottom"]),
                },
                "query_string": self.request_query_string,
            },
        )

    move_up_down_links.short_description = _("Move")


class OrderedTabularInline(OrderedInlineMixin, admin.TabularInline):
    pass


class OrderedStackedInline(OrderedInlineMixin, admin.StackedInline):
    pass


class DragDropOrderedModelAdmin(BaseOrderedModelAdmin, admin.ModelAdmin):
    def get_urls(self):
        from django.urls import path

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)

            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        return [
            path(
                "<path:object_id>/move-above/<path:other_object_id>/",
                wrap(self.move_above_view),
                name="{app}_{model}_order_above".format(**self._get_model_info()),
            )
        ] + super().get_urls()

    def move_above_view(self, request, object_id, other_object_id):
        obj = get_object_or_404(self.model, pk=unquote(object_id))
        other_obj = get_object_or_404(self.model, pk=unquote(other_object_id))
        obj.above(other_obj)
        # go back 3 levels (to get from /pk/move-above/other-pk back to the changelist)
        return HttpResponseRedirect("../../../")

    def make_draggable(self, obj):
        model_info = self._get_model_info()
        url = reverse(
            "{admin_name}:{app}_{model}_order_above".format(
                admin_name=self.admin_site.name, **model_info
            ),
            args=[-1, 0],  # placeholder pks, will be replaced in js
        )
        return mark_safe(
            """
        <div class="pk-holder" data-pk="%s"></div> <!-- render the pk into each row -->
        <style>[draggable=true] { -khtml-user-drag: element; }</style>  <!-- fix for dragging in safari -->
        <script>
            window.__draggedObjPk = null;
            django.jQuery(function () {
                const $ = django.jQuery;
                if (!window.__listSortableSemaphore) {  // make sure this part only runs once
                    window.__move_to_url = '%s'; // this is the url including the placeholder pks
                    $('#result_list > tbody > tr').each(function(idx, tr) {
                        const $tr = $(tr);
                        $tr.attr('draggable', 'true');
                        const pk = $tr.find('.pk-holder').attr('data-pk');
                        $tr.attr('data-pk', pk);
                        $tr.on('dragstart', function (event) {
                            event.originalEvent.dataTransfer.setData('text/plain', null);  // make draggable work in firefox
                            window.__draggedObjPk = $(this).attr('data-pk');
                        });
                        $tr.on('dragover', false); // make it droppable
                        $tr.on('drop', function (event) {
                            event.preventDefault();  // prevent firefox from opening the dataTransfer data
                            const otherPk = $(this).attr('data-pk');
                            console.log(window.__draggedObjPk, 'dropped on', otherPk);
                            const url = window.__move_to_url
                                .replace('\/0\/', '/' + otherPk + '/')
                                .replace('\/-1\/', '/' + window.__draggedObjPk + '/');
                            console.log('redirecting', url);
                            window.location = url;
                        });
                    });
                    window.__listSortableSemaphore = true;
                }
            });
        </script>
        """
            % (obj.pk, url)
        )

    make_draggable.allow_tags = True
    make_draggable.short_description = ""
