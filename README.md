# Ironleaf Trading & Contrac ing: website

Five static pages, English and Arabic, no build step and no dependencies. Open `index.html` in a browser or upload the whole folder to any host.

```
index.html        Home
about.html        About us
services.html     Services (Trading + Contracting)
trading.html      Trading
contact.html      Contact
style.css
main.js
IronleaLogoPNG.png
banner.png
```

## Editing text

Every piece of copy carries both languages on the same tag:

```html
<h3 data-en="Trading" data-ar="التجارة">Trading</h3>
```

The visible text is English; `main.js` swaps in `data-ar` when Arabic is selected and flips the page to RTL. To change wording, edit both attributes **and** the visible text. Placeholders use `data-en-ph` / `data-ar-ph`.

One rule: a tag that wraps other translated tags must not carry `data-en` itself. Put the text in its own `<span>` instead.

## Editing the design

All colours, fonts and spacing live in the `:root` block at the top of `style.css`. Changing `--gold` or `--ink` restyles the whole site.

## Placeholder content still to fill in
 
Several fields weren't available when this site was built and are marked `[Data not shared]` (or similar) directly in the page copy so they're easy to find and replace:

- **Office address**: footer and contact page.
- **Email address(es)**: footer, contact page, and `CONTACT_EMAIL` in `main.js` (currently blank, so the enquiry form tells visitors to call instead of opening a mail app).
- **Office hours**: contact page.
- **Certifications**: services page FAQ.
- **Specific product / material and project / trade categories**: trading and services pages currently just invite visitors to ask.

Once an email address is confirmed, set `CONTACT_EMAIL` near the top of the `4c. Enquiry form` section in `main.js` and the form will go back to opening the visitor's mail app.

## Before going live

- Fill in the placeholders listed above.
- Replace the LinkedIn and Instagram links in the footer with the real profiles (or remove them).
- Confirm the WhatsApp number in the footer and contact page; it currently reuses the main phone number, +974 3001 3636.
- Add a `favicon.ico` and an Open Graph image if you want link previews.
