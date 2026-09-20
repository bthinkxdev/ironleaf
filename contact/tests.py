import time
from unittest import mock

from django.core import mail, signing
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from . import captcha
from .models import ContactMessage
from .views import TS_SALT

XHR = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CONTACT_RECIPIENT_EMAIL=["office@example.com"],
    DEFAULT_FROM_EMAIL="site@example.com",
    CONTACT_MIN_FILL_SECONDS=0,
    CAPTCHA_LENGTH=5,
)
class ContactFormTests(TestCase):
    url = "/contact/"

    def setUp(self):
        self.client = Client()

    def _issue(self, _code="A"):
        """Request a captcha image with a known code (every character is 'A')."""
        with mock.patch.object(captcha, "ALPHABET", "A"):
            resp = self.client.get(reverse("contact:captcha"))
        self.assertEqual(resp.status_code, 200)
        return "AAAAA"

    def _payload(self, **extra):
        page = self.client.get(self.url)
        data = {
            "name": "Sara Ahmed", "company": "Acme", "email": "sara@example.com", "phone": "",
            "service": "Trading", "message": "We need 200 bags of cement delivered next week.",
            "captcha": "AAAAA", "website": "", "ts": page.context["form_ts"],
        }
        data.update(extra)
        return data

    def _post(self, data):
        return self.client.post(self.url, data, **XHR)

    # -- pages ---------------------------------------------------------
    def test_page_renders_with_captcha_and_csrf(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, "csrfmiddlewaretoken")
        self.assertContains(resp, reverse("contact:captcha"))
        self.assertContains(resp, 'name="website"')

    def test_captcha_image_is_png_and_uncached(self):
        resp = self.client.get(reverse("contact:captcha"))
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertTrue(resp.content.startswith(b"\x89PNG"))
        self.assertIn("no-store", resp["Cache-Control"])

    # -- happy path ----------------------------------------------------
    def test_valid_submission_saves_and_emails(self):
        self._issue("A")
        resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(ContactMessage.objects.count(), 1)
        self.assertTrue(ContactMessage.objects.get().email_sent)
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertEqual(sent.to, ["office@example.com"])
        self.assertEqual(sent.reply_to, ["sara@example.com"])
        self.assertIn("cement", sent.body)

    def test_plain_post_redirects_after_success(self):
        self._issue("A")
        resp = self.client.post(self.url, self._payload())
        self.assertRedirects(resp, self.url, fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)

    # -- captcha -------------------------------------------------------
    def test_wrong_captcha_is_rejected(self):
        self._issue("A")
        resp = self._post(self._payload(captcha="ZZZZZ"))
        self.assertEqual(resp.json()["code"], "captcha")
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_captcha_is_rejected(self):
        self._issue("A")
        resp = self._post(self._payload(captcha=""))
        self.assertFalse(resp.json()["ok"])
        self.assertEqual(len(mail.outbox), 0)

    def test_captcha_is_single_use(self):
        self._issue("A")
        first = self._post(self._payload())
        self.assertTrue(first.json()["ok"])
        replay = self._post(self._payload())
        self.assertEqual(replay.json()["code"], "captcha")
        self.assertEqual(len(mail.outbox), 1)

    def test_failed_guess_burns_the_challenge(self):
        self._issue("A")
        self.assertEqual(self._post(self._payload(captcha="BBBBB")).json()["code"], "captcha")
        self.assertEqual(self._post(self._payload(captcha="AAAAA")).json()["code"], "captcha")

    def test_no_captcha_issued_at_all(self):
        resp = self._post(self._payload())
        self.assertEqual(resp.json()["code"], "captcha")

    @override_settings(CAPTCHA_TTL_SECONDS=-1)
    def test_expired_captcha_is_rejected(self):
        self._issue("A")
        self.assertEqual(self._post(self._payload()).json()["code"], "captcha")

    def test_captcha_is_case_and_space_insensitive(self):
        self._issue("A")
        self.assertTrue(self._post(self._payload(captcha=" aa aaa ")).json()["ok"])

    # -- honeypot / timing --------------------------------------------
    def test_honeypot_fakes_success_but_sends_nothing(self):
        self._issue("A")
        resp = self._post(self._payload(website="http://spam.example"))
        self.assertTrue(resp.json()["ok"])
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CONTACT_MIN_FILL_SECONDS=30)
    def test_too_fast_submission_is_rejected(self):
        self._issue("A")
        self.assertEqual(self._post(self._payload()).json()["code"], "too_fast")
        self.assertEqual(len(mail.outbox), 0)

    def test_tampered_timestamp_is_rejected(self):
        self._issue("A")
        self.assertEqual(self._post(self._payload(ts="forged")).json()["code"], "expired")

    def test_stale_timestamp_is_rejected(self):
        self._issue("A")
        with mock.patch("django.core.signing.time.time", return_value=time.time() - 99999):
            stale = signing.dumps(time.time(), salt=TS_SALT)
        self.assertEqual(self._post(self._payload(ts=stale)).json()["code"], "expired")

    # -- validation ----------------------------------------------------
    def test_needs_email_or_phone(self):
        self._issue("A")
        resp = self._post(self._payload(email="", phone=""))
        self.assertEqual(resp.json()["code"], "need_contact")

    def test_phone_only_is_fine(self):
        self._issue("A")
        self.assertTrue(self._post(self._payload(email="", phone="+974 6686 1283")).json()["ok"])

    def test_invalid_email_and_phone(self):
        self._issue("A")
        resp = self._post(self._payload(email="nope", phone="abc"))
        self.assertEqual(resp.json()["code"], "invalid")
        self.assertCountEqual(resp.json()["fields"], ["email", "phone"])

    def test_link_spam_rejected(self):
        self._issue("A")
        msg = "Buy now http://a.example http://b.example http://c.example please"
        self.assertEqual(self._post(self._payload(message=msg)).json()["code"], "spam")

    def test_header_injection_is_neutralised(self):
        self._issue("A")
        resp = self._post(self._payload(name="Sara\nBcc: victim@example.com"))
        self.assertTrue(resp.json()["ok"])
        sent = mail.outbox[0]
        self.assertNotIn("\n", sent.subject)
        self.assertNotIn("victim@example.com", "".join(sent.extra_headers.values()) + "".join(sent.bcc))

    # -- rate limits ---------------------------------------------------
    @override_settings(CONTACT_MAX_PER_HOUR=2)
    def test_per_ip_rate_limit(self):
        for _ in range(2):
            ContactMessage.objects.create(name="x", service="Trading", message="0123456789", ip_address="127.0.0.1")
        self._issue("A")
        resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 429)
        self.assertEqual(resp.json()["code"], "rate_limited")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(CONTACT_ATTEMPTS_PER_HOUR=2)
    def test_per_session_attempt_limit(self):
        self._issue("A")
        for _ in range(2):
            self._post(self._payload(captcha="ZZZZZ"))
        self.assertEqual(self._post(self._payload()).json()["code"], "rate_limited")

    @override_settings(CAPTCHA_IMAGE_LIMIT=2)
    def test_captcha_image_request_limit(self):
        codes = [self.client.get(reverse("contact:captcha")).status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])

    def test_x_forwarded_for_ignored_unless_proxy_configured(self):
        self._issue("A")
        self.client.post(self.url, self._payload(), HTTP_X_FORWARDED_FOR="9.9.9.9", **XHR)
        self.assertEqual(ContactMessage.objects.get().ip_address, "127.0.0.1")

    @override_settings(TRUSTED_PROXY_COUNT=1)
    def test_x_forwarded_for_used_behind_trusted_proxy(self):
        self._issue("A")
        self.client.post(self.url, self._payload(), HTTP_X_FORWARDED_FOR="1.1.1.1, 9.9.9.9", **XHR)
        self.assertEqual(ContactMessage.objects.get().ip_address, "9.9.9.9")

    # -- csrf / email failure -----------------------------------------
    def test_csrf_is_enforced(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(self.url, {"name": "x"}).status_code, 403)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.dummy.EmailBackend")
    def test_email_failure_keeps_the_enquiry(self):
        self._issue("A")
        with mock.patch("contact.views.EmailMessage.send", side_effect=OSError("smtp down")):
            resp = self._post(self._payload())
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.json()["code"], "email_failed")
        self.assertFalse(ContactMessage.objects.get().email_sent)

    @override_settings(CONTACT_RECIPIENT_EMAIL=[])
    def test_no_recipient_configured_is_reported(self):
        self._issue("A")
        self.assertEqual(self._post(self._payload()).json()["code"], "email_failed")

    def test_get_only_for_captcha_image(self):
        self.assertEqual(self.client.post(reverse("contact:captcha")).status_code, 405)


class CaptchaUnitTests(TestCase):
    def test_render_png_is_valid(self):
        data = captcha.render_png("ABCDE")
        self.assertTrue(data.startswith(b"\x89PNG"))
        self.assertGreater(len(data), 2000)

    def test_code_uses_unambiguous_alphabet(self):
        for ch in "ILO01":
            self.assertNotIn(ch, captcha.ALPHABET)
