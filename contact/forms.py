import re

from django import forms
from django.core.exceptions import ValidationError

SERVICES = ["Trading", "Contracting", "Something else"]
PHONE_RE = re.compile(r"^\+?[0-9][0-9 ()\-]{5,28}$")
LINK_RE = re.compile(r"https?://|www\.|\.(?:com|net|org|ru|xyz|top|info)/", re.IGNORECASE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _single_line(value):
    """Collapse whitespace and drop control characters (blocks header injection)."""
    return " ".join(CONTROL_RE.sub("", value).split())


class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    company = forms.CharField(max_length=120, required=False)
    email = forms.EmailField(max_length=254, required=False)
    phone = forms.CharField(max_length=30, required=False)
    service = forms.ChoiceField(choices=[(s, s) for s in SERVICES])
    message = forms.CharField(min_length=10, max_length=3000)
    captcha = forms.CharField(max_length=8)

    def clean_name(self):
        value = _single_line(self.cleaned_data["name"])
        if not value:
            raise ValidationError("Required.", code="required")
        return value

    def clean_company(self):
        return _single_line(self.cleaned_data.get("company", ""))

    def clean_phone(self):
        value = _single_line(self.cleaned_data.get("phone", ""))
        if value and not PHONE_RE.match(value):
            raise ValidationError("Enter a valid phone number.", code="invalid_phone")
        return value

    def clean_message(self):
        value = CONTROL_RE.sub("", self.cleaned_data["message"]).strip()
        if len(value) < 10:
            raise ValidationError("Too short.", code="min_length")
        if len(LINK_RE.findall(value)) > 2:
            raise ValidationError("Too many links.", code="spam")
        return value

    def clean(self):
        cleaned = super().clean()
        # Only complain about a missing contact method once the individual
        # email/phone fields are themselves valid.
        if not self.errors.get("email") and not self.errors.get("phone"):
            if not cleaned.get("email") and not cleaned.get("phone"):
                raise ValidationError("Add an email or a phone number.", code="need_contact")
        return cleaned
