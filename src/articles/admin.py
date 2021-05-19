from django.contrib import admin
from .models import Article

class ArticleAdmin(admin.ModelAdmin):
    list_display = ("name", "published", "created_on", "last_updated", "price",)
    list_editable = ("published", "price",)

admin.site.register(Article, ArticleAdmin)