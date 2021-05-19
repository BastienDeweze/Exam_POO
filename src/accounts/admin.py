from django.contrib import admin
from .models import UserProfile

class ArticleAdmin(admin.ModelAdmin):
    list_display = ("user", "first_name", "last_name", "created_on", "updated_on",)

admin.site.register(UserProfile, ArticleAdmin)