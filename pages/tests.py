from django.test import TestCase
from django.urls import reverse


class PageTests(TestCase):
    def test_every_page_renders_and_marks_active_nav(self):
        for name, key in (("pages:home", "home"), ("pages:about", "about"),
                          ("pages:services", "services"), ("pages:trading", "trading"),
                          ("contact:contact", "contact")):
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 200, name)
            self.assertEqual(resp.context["active"], key)
            self.assertContains(resp, 'aria-current="page"')
            self.assertContains(resp, "+974 3001 3636")

    def test_no_leftover_placeholders(self):
        for name in ("pages:home", "pages:about", "pages:services", "pages:trading", "contact:contact"):
            body = self.client.get(reverse(name)).content.decode()
            self.assertNotIn("not shared", body)

    def test_custom_404(self):
        resp = self.client.get("/does-not-exist/")
        self.assertEqual(resp.status_code, 404)
        self.assertContains(resp, "Page not found", status_code=404)

    def test_robots(self):
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp["Content-Type"], "text/plain")
        self.assertContains(resp, "Disallow: /admin/")
