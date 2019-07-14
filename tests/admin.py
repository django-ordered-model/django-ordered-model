from django.contrib import admin

from ordered_model.admin import (
    OrderedModelAdmin,
    OrderedTabularInline,
    OrderedInlineModelAdminMixin,
)

from .models import Item, PizzaToppingsThroughModel, Pizza


class ItemAdmin(OrderedModelAdmin):
    list_display = ("name", "move_up_down_links")


class PizzaToppingTabularInline(OrderedTabularInline):
    model = PizzaToppingsThroughModel
    fields = ("order", "move_up_down_links")
    readonly_fields = ("order", "move_up_down_links")
    ordering = ("order",)


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = Pizza
    list_display = ("name",)
    inlines = (PizzaToppingTabularInline,)


admin.site.register(Item, ItemAdmin)
admin.site.register(Pizza, PizzaAdmin)
