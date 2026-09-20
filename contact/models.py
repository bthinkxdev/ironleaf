from django.db import models


class ContactMessage(models.Model):
    """Every enquiry is stored, so nothing is lost if email delivery fails."""

    name = models.CharField(max_length=100)
    company = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    service = models.CharField(max_length=40)
    message = models.TextField(max_length=3000)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.CharField(max_length=300, blank=True)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return "%s (%s)" % (self.name, self.service)
