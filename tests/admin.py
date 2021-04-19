from django.contrib import admin

from ordered_model.admin import (
    OrderedModelAdmin,
    OrderedTabularInline,
    OrderedStackedInline,
    OrderedInlineModelAdminMixin,
)

from .models import (
    Item,
    PizzaToppingsThroughModel,
    Pizza,
    PizzaProxy,
    Topping,
    CustomPKGroupItem,
    CustomPKGroup,
)

# README example for OrderedModelAdmin
class ItemAdmin(OrderedModelAdmin):
    list_display = ("name", "move_up_down_links")


# README example for TabularInline
class PizzaToppingTabularInline(OrderedTabularInline):
    model = PizzaToppingsThroughModel
    fields = ("topping", "order", "move_up_down_links")
    readonly_fields = ("order", "move_up_down_links")
    ordering = ("order",)
    extra = 1


class PizzaAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = Pizza
    list_display = ("name",)
    inlines = (PizzaToppingTabularInline,)


# README example for StackedInline
class PizzaToppingStackedInline(OrderedStackedInline):
    model = PizzaToppingsThroughModel
    fields = ("topping", "move_up_down_links")
    readonly_fields = ("move_up_down_links",)
    ordering = ("order",)
    extra = 1


class PizzaProxyAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = PizzaProxy
    list_display = ("name",)
    inlines = (PizzaToppingStackedInline,)


class CustomPKGroupItemInline(OrderedTabularInline):
    model = CustomPKGroupItem
    fields = ("name", "order", "move_up_down_links")
    readonly_fields = ("order", "move_up_down_links")


class CustomPKGroupAdmin(OrderedInlineModelAdminMixin, admin.ModelAdmin):
    model = CustomPKGroup
    inlines = (CustomPKGroupItemInline,)


admin.site.register(Item, ItemAdmin)
admin.site.register(Pizza, PizzaAdmin)
admin.site.register(PizzaProxy, PizzaProxyAdmin)
admin.site.register(Topping)
admin.site.register(CustomPKGroup, CustomPKGroupAdmin)
