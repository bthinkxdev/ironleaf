import logging
import time
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.core.mail import EmailMessage
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods

from . import captcha
from .forms import ContactForm
from .models import ContactMessage

logger = logging.getLogger(__name__)

TS_SALT = "contact-form-timestamp"

MESSAGES = {
    "sent": "Thank you. Your enquiry has been sent and we will be in touch shortly.",
    "invalid": "Please check the highlighted fields and try again.",
    "need_contact": "Please add an email or a phone number so we can reply.",
    "spam": "Please remove the links from your message and try again.",
    "captcha": "The security code was incorrect or has expired. Please try the new code.",
    "too_fast": "That was very quick. Please wait a moment and try again.",
    "expired": "This form has expired. Please reload the page and try again.",
    "rate_limited": "Too many enquiries from your connection. Please try again later or call us.",
    "email_failed": "We could not send your enquiry right now. Please call or WhatsApp us on +974 6686 1283.",
    "error": "Something went wrong. Please reload the page and try again.",
}
STATUS_CODES = {"sent": 200, "invalid": 400, "need_contact": 400, "spam": 400, "captcha": 400,
                "too_fast": 400, "expired": 400, "rate_limited": 429, "email_failed": 502}


def client_ip(request):
    """Client IP. Only trusts X-Forwarded-For when a proxy count is configured."""
    hops = settings.TRUSTED_PROXY_COUNT
    if hops > 0:
        parts = [p.strip() for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]
        if len(parts) >= hops:
            return parts[-hops]
    return request.META.get("REMOTE_ADDR") or None


def _wants_json(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")


def _new_form_ts():
    return signing.dumps(time.time(), salt=TS_SALT)


def _respond(request, code, form=None, fields=None):
    ok = code == "sent"
    if _wants_json(request):
        return JsonResponse({"ok": ok, "code": code, "message": MESSAGES[code], "fields": fields or []},
                            status=STATUS_CODES.get(code, 400))
    if ok:
        request.session["contact_flash"] = code
        return redirect("contact:contact")
    return _render(request, form or ContactForm(), status=MESSAGES[code], http_status=STATUS_CODES.get(code, 400))


def _render(request, form, status="", ok=False, http_status=200):
    response = render(request, "contact/contact.html", {
        "active": "contact", "form": form, "form_ts": _new_form_ts(), "status": status, "status_ok": ok,
    }, status=http_status)
    response["Cache-Control"] = "no-store"
    return response


def _attempt_allowed(request):
    now = time.time()
    attempts = [t for t in request.session.get("contact_attempts", []) if now - t < 3600]
    if len(attempts) >= settings.CONTACT_ATTEMPTS_PER_HOUR:
        request.session["contact_attempts"] = attempts
        return False
    attempts.append(now)
    request.session["contact_attempts"] = attempts
    return True


def _over_rate_limit(ip):
    if not ip:
        return False
    now = timezone.now()
    recent = ContactMessage.objects.filter(ip_address=ip)
    return (recent.filter(created_at__gte=now - timedelta(hours=1)).count() >= settings.CONTACT_MAX_PER_HOUR
            or recent.filter(created_at__gte=now - timedelta(days=1)).count() >= settings.CONTACT_MAX_PER_DAY)


def _deliver(msg):
    recipients = settings.CONTACT_RECIPIENT_EMAIL
    if not recipients:
        logger.error("CONTACT_RECIPIENT_EMAIL is not configured; enquiry %s was saved only.", msg.pk)
        return False
    subject = "Website enquiry: %s from %s" % (msg.service, msg.name)
    lines = [
        "New enquiry from the website",
        "",
        "Name:     %s" % msg.name,
        "Company:  %s" % (msg.company or "-"),
        "Email:    %s" % (msg.email or "-"),
        "Phone:    %s" % (msg.phone or "-"),
        "Service:  %s" % msg.service,
        "",
        "Message:",
        msg.message,
        "",
        "-- Sent %s from IP %s" % (timezone.localtime(msg.created_at).strftime("%Y-%m-%d %H:%M"), msg.ip_address or "unknown"),
    ]
    email = EmailMessage(subject[:150], "\n".join(lines), settings.DEFAULT_FROM_EMAIL, recipients,
                         reply_to=[msg.email] if msg.email else None)
    try:
        email.send(fail_silently=False)
    except Exception:
        logger.exception("Could not send enquiry %s by email.", msg.pk)
        return False
    return True


@never_cache
@require_http_methods(["GET", "POST"])
def contact(request):
    if request.method == "GET":
        flash = request.session.pop("contact_flash", "")
        return _render(request, ContactForm(), status=MESSAGES.get(flash, ""), ok=flash == "sent")

    if not _attempt_allowed(request):
        return _respond(request, "rate_limited")

    form = ContactForm(request.POST)

    # 1. Honeypot: real visitors never see this field. Pretend success so bots move on.
    if request.POST.get("website", "").strip():
        logger.warning("Honeypot triggered from %s", client_ip(request))
        return _respond(request, "sent")

    # 2. Signed timestamp: the form must have been served by us, not too fast, not stale.
    try:
        rendered_at = signing.loads(request.POST.get("ts", ""), salt=TS_SALT, max_age=settings.CONTACT_FORM_MAX_AGE_SECONDS)
    except signing.BadSignature:
        return _respond(request, "expired", form)
    if time.time() - float(rendered_at) < settings.CONTACT_MIN_FILL_SECONDS:
        return _respond(request, "too_fast", form)

    # 3. Field validation (does not consume the captcha, so typos are cheap).
    if not form.is_valid():
        errors = form.errors.as_data()
        codes = {e.code for errs in errors.values() for e in errs}
        code = "need_contact" if "need_contact" in codes else "spam" if "spam" in codes else "invalid"
        return _respond(request, code, form, fields=[f for f in errors if f != "__all__"])

    # 4. Captcha, checked on the server against the session. Always single use.
    if not captcha.verify(request, form.cleaned_data["captcha"]):
        return _respond(request, "captcha", form, fields=["captcha"])

    # 5. Per-IP limits, then store and send.
    ip = client_ip(request)
    if _over_rate_limit(ip):
        return _respond(request, "rate_limited", form)

    data = form.cleaned_data
    msg = ContactMessage.objects.create(
        name=data["name"], company=data["company"], email=data["email"], phone=data["phone"],
        service=data["service"], message=data["message"], ip_address=ip,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
    if not _deliver(msg):
        return _respond(request, "email_failed", form)
    msg.email_sent = True
    msg.save(update_fields=["email_sent"])
    return _respond(request, "sent")


@never_cache
@require_GET
def captcha_image(request):
    if not captcha.allow_new_image(request):
        return HttpResponse("Too many requests.", status=429, content_type="text/plain")
    code = captcha.issue(request)
    response = HttpResponse(captcha.render_png(code), content_type="image/png")
    response["Cache-Control"] = "no-store, max-age=0"
    response["X-Content-Type-Options"] = "nosniff"
    return response
