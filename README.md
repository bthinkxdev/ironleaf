# Land Creation Contracting — website

Five static pages, English and Arabic, no build step and no dependencies. Open `index.html` in a browser or upload the whole folder to any host.

```
index.html        Home
about.html        About us
services.html     Services
manpower.html     Skilled manpower
contact.html      Contact
assets/css/style.css
assets/js/main.js
build.py          optional generator (rebuilds the 5 pages from shared partials)
```

## Editing text

Every piece of copy carries both languages on the same tag:

```html
<h3 data-en="Maintenance" data-ar="الصيانة">Maintenance</h3>
```

The visible text is English; `main.js` swaps in `data-ar` when Arabic is selected and flips the page to RTL. To change wording, edit both attributes **and** the visible text. Placeholders use `data-en-ph` / `data-ar-ph`.

One rule: a tag that wraps other translated tags must not carry `data-en` itself. Put the text in its own `<span>` instead.

## Editing the design

All colours, fonts and spacing live in the `:root` block at the top of `style.css`. Changing `--gold` or `--ink` restyles the whole site.

## The contact form

There is no server, so submitting opens the visitor's mail app with the enquiry pre-filled and addressed to `info@landcreationcontracting.com`. To collect submissions properly, point the form at a service such as Formspree or your own endpoint — replace the `form.addEventListener('submit', …)` block in `main.js`.

## Before going live

- Replace the LinkedIn and Instagram links in the footer with the real profiles.
- Confirm the office hours on the contact page.
- Add a `favicon.ico` and an Open Graph image if you want link previews.
- The brochure mentions the UAE in one line; the site says Qatar throughout, matching the Doha address.
