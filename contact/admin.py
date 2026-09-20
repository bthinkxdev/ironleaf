from django.contrib import admin

from .models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "name", "service", "email", "phone", "email_sent", "ip_address")
    list_filter = ("service", "email_sent", "created_at")
    search_fields = ("name", "company", "email", "phone", "message")
    readonly_fields = [f.name for f in ContactMessage._meta.fields]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False
