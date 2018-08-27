from django.contrib import admin
from ordered_model.admin import OrderedModelAdmin, OrderedTabularInline
from .models import Item, PizzaToppingsThroughModel, Pizza


class ItemAdmin(OrderedModelAdmin):
    list_display = ('name', 'move_up_down_links')


class PizzaToppingTabularInline(OrderedTabularInline):
    model = PizzaToppingsThroughModel
    fields = ('order', 'move_up_down_links',)
    readonly_fields = ('order', 'move_up_down_links',)
    ordering = ('order',)


class PizzaAdmin(admin.ModelAdmin):
    model = Pizza
    list_display = ('name',)
    inlines = (PizzaToppingTabularInline,)

    def get_urls(self):
        urls = super(PizzaAdmin, self).get_urls()
        for inline in self.inlines:
            if hasattr(inline, 'get_urls'):
                urls = inline.get_urls(self) + urls
        return urls


admin.site.register(Item, ItemAdmin)
admin.site.register(Pizza, PizzaAdmin)
