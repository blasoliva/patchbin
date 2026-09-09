from django.contrib import admin
from django.db.models import Count

from .models import ConnectorFamily, ConnectorType


class ConnectorTypeInline(admin.TabularInline):
    model = ConnectorType
    extra = 0
    fields = ("name", "abbreviation", "contact_count", "is_active", "sort_order")
    show_change_link = True
    # slug is left off here on purpose: it is a compact row, and the model
    # auto-fills the slug from the name on save.


@admin.register(ConnectorFamily)
class ConnectorFamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "type_count", "sort_order")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")
    inlines = [ConnectorTypeInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_type_count=Count("types"))

    @admin.display(description="types", ordering="_type_count")
    def type_count(self, obj):
        return obj._type_count


@admin.register(ConnectorType)
class ConnectorTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "family", "abbreviation", "contact_count", "is_active")
    list_filter = ("family", "is_active")
    search_fields = ("name", "abbreviation", "description", "typical_uses")
    prepopulated_fields = {"slug": ("name",)}
    list_select_related = ("family",)
    ordering = ("family__sort_order", "family__name", "sort_order", "name")
