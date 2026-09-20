# Ironleaf Trading & Contracting: Django website

A Django project serving the bilingual (English / Arabic) company site, with a
contact form that emails enquiries through Gmail SMTP and is protected by a
server-validated captcha.

```
config/            project settings (all secrets come from .env), urls, wsgi
pages/             app: Home, About, Services, Trading, 404/500 handlers
contact/           app: contact form, captcha, email delivery, ContactMessage model
templates/         base.html (shared header/footer) + one template per page
static/            css/style.css, js/main.js, img/ (logo, banner, icons), video/hero.mp4 (home banner)
source/            original full-size logo, banner and video (not needed to run)
.env.example       every setting, documented
requirements.txt
```

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env  (then edit it)
python manage.py migrate
python manage.py createsuperuser  # to read enquiries at /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000/. With `DJANGO_DEBUG=True` and no Gmail credentials,
emails are printed to the terminal instead of being sent.

## Gmail SMTP setup (contact form email)

1. On the Gmail account that will send the mail, turn on **2-Step Verification**.
2. Create an **App Password**: Google Account > Security > App passwords.
3. Put these in `.env`:

```
EMAIL_HOST_USER=your.address@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx     # the 16-character app password
CONTACT_RECIPIENT_EMAIL=where.enquiries.go@example.com
```

The visitor's email (when given) is set as the message's `Reply-To`, so replying
to the enquiry goes straight to them. Every enquiry is also saved in the
database (`/admin/` > Contact messages), so nothing is lost if Gmail is down;
the visitor is then asked to call or WhatsApp instead.

## How the captcha and bot protection work

Everything is verified on the server. The browser never receives the answer.

| Layer | What it does |
| --- | --- |
| Image captcha | Server draws a distorted PNG; the session stores only a salted HMAC of the code. Case and spaces are ignored. |
| Single use | Every verification attempt burns the code, so a bot cannot keep guessing one image. |
| Expiry | Codes expire after `CAPTCHA_TTL_SECONDS` (default 10 minutes). |
| Honeypot | Hidden `website` field. If filled, the bot is told "sent" and nothing is saved or emailed. |
| Signed timestamp | The form carries a signed render time. Forged, stale (>2h) or too-fast (< `CONTACT_MIN_FILL_SECONDS`) posts are rejected. |
| CSRF | Django's CSRF token is required. |
| Rate limits | Per browser session (attempts and new captcha images) and per IP (`CONTACT_MAX_PER_HOUR` / `CONTACT_MAX_PER_DAY`, stored in the database so it holds across workers). |
| Content rules | Server-side validation, header-injection stripping, and more than two links in a message is rejected. |

Behind a reverse proxy or CDN, set `TRUSTED_PROXY_COUNT` (for example `1`) so the
per-IP limit sees the real visitor address. It is ignored when `0`, which stops
visitors spoofing `X-Forwarded-For`.

Accessibility note: an image captcha is hard for screen-reader users, so the
contact page also shows the phone, mobile and WhatsApp numbers.

Run the tests (35, covering all of the above): `python manage.py test`

## Deploying

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi --bind 0.0.0.0:8000
```

Production `.env` essentials:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long random string>
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DJANGO_BEHIND_PROXY=True         # if a proxy/PaaS terminates HTTPS
DJANGO_ADMIN_URL=some-private-path/
```

With `DJANGO_DEBUG=False`, HTTPS redirect, secure cookies and HSTS are switched on
automatically, and static files are served (compressed, fingerprinted) by WhiteNoise.
`python manage.py check --deploy` should report no problems.

The default database is SQLite (`db.sqlite3`, or `DATABASE_PATH`). Keep it on
persistent storage, and back it up if you want a record of enquiries.

## Banners and loader

- **Home** uses `static/video/hero.mp4` (compressed from `source/Construction_company.mp4`, 2.2 MB, muted, looping) with `img/hero-poster.jpg` as the fallback frame. It is hidden for visitors who prefer reduced motion.
- **About, Services, Trading and Contact** use `img/banner.jpg` (from `source/banner.png`) behind a navy overlay for text contrast. The overlay strengths are in `.hero-overlay` and `.page-hero` in `style.css`.
- **Loader**: every page starts with the logo on screen. The logo stays for a fixed minimum time (`LOADER_MIN_MS` in section 0 of `main.js`, currently 1000 ms, and never before the page has loaded), then "blasts" out of a soft white circle and the content rises in. Change `LOADER_MIN_MS` to make it longer or shorter; if scripts fail, an 8-second failsafe in `base.html` reveals the page anyway.

## Editing content

Every piece of copy carries both languages on the same tag:

```html
<h3 data-en="Trading" data-ar="التجارة">Trading</h3>
```

The visible text is English; `static/js/main.js` swaps in `data-ar` when Arabic
is selected and flips the page to RTL. To change wording, edit both attributes
**and** the visible text. Shared header and footer live in `templates/base.html`.
Colours, fonts and spacing are in the `:root` block of `static/css/style.css`.

## Business details used on the site

- Phone: +974 3001 3636
- Mobile and WhatsApp: +974 6686 1283
- Address: Building 92, Street 631, Zone 74, Qatar (map link and embed on Home and Contact)
- Commercial Registration: 247549, established 2026

## Please confirm before going live

- **Product and service categories** on the Trading and Services pages were written from typical trading and contracting scope in Qatar. Edit them to match what Ironleaf actually offers.
- **Public email address, office hours, certifications**: none supplied, so none are shown.
- Replace the LinkedIn and Instagram links in the footer with the real profiles (or remove them).
- Once the domain is known, add canonical links, an `og:image` (needs an absolute URL) and a sitemap.
