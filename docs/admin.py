from django.contrib import admin
from .models import BeltLevel, Technique, Document

@admin.register(BeltLevel)
class BeltLevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order", "is_public")
    list_editable = ("order", "is_public")
    search_fields = ("name",)

@admin.register(Technique)
class TechniqueAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "level")
    list_filter = ("level",)
    search_fields = ("name", "description")

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "visibility", "created_at")
    list_filter = ("visibility",)
    search_fields = ("title",)
