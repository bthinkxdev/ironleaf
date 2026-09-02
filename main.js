/* ==========================================================================
   Ironleaf Trading & Contrac ing: site behaviour
   1. Language      EN / AR with full RTL mirroring
   2. Navigation    fixed header states + mobile drawer
   3. Motion        scroll reveals (skipped when reduced motion is requested)
   4. Components    accordion, back to top, enquiry form
   ========================================================================== */
(function () {
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- small storage helper (never throws) ---------- */
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* private mode */ } }
  };

  /* ======================================================================
     1. Language
     Every translatable node carries data-en / data-ar. Placeholders use
     data-en-ph / data-ar-ph, labels for icons use data-en-aria / data-ar-aria.
     ====================================================================== */
  var LANG_KEY = 'lc-lang';

  function applyLang(lang) {
    var isAr = lang === 'ar';

    root.setAttribute('lang', lang);
    root.setAttribute('dir', isAr ? 'rtl' : 'ltr');

    doc.querySelectorAll('[data-en]').forEach(function (el) {
      // A node that wraps other translatable nodes is a container, not a string.
      if (el.querySelector('[data-en]')) return;
      var val = el.getAttribute(isAr ? 'data-ar' : 'data-en');
      if (val !== null) el.textContent = val;
    });

    doc.querySelectorAll('[data-en-ph]').forEach(function (el) {
      var val = el.getAttribute(isAr ? 'data-ar-ph' : 'data-en-ph');
      if (val !== null) el.setAttribute('placeholder', val);
    });

    doc.querySelectorAll('[data-en-aria]').forEach(function (el) {
      var val = el.getAttribute(isAr ? 'data-ar-aria' : 'data-en-aria');
      if (val !== null) el.setAttribute('aria-label', val);
    });

    doc.querySelectorAll('.lang-btn').forEach(function (btn) {
      btn.setAttribute('aria-label', isAr ? 'التبديل إلى الإنجليزية' : 'Switch to Arabic');
    });

    store.set(LANG_KEY, lang);
  }

  function currentLang() {
    return root.getAttribute('lang') === 'ar' ? 'ar' : 'en';
  }

  applyLang(store.get(LANG_KEY) === 'ar' ? 'ar' : 'en');

  doc.querySelectorAll('.lang-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      applyLang(currentLang() === 'ar' ? 'en' : 'ar');
      closeDrawer();
    });
  });

  /* ======================================================================
     2. Header + drawer
     ====================================================================== */
  var header = doc.querySelector('.header');
  var burger = doc.querySelector('.burger');
  var scrim = doc.querySelector('.scrim');

  function onScroll() {
    if (header) header.classList.toggle('is-solid', window.scrollY > 18);
    var top = doc.querySelector('.to-top');
    if (top) top.classList.toggle('is-visible', window.scrollY > 520);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  function openDrawer() {
    doc.body.classList.add('nav-open');
    if (burger) burger.setAttribute('aria-expanded', 'true');
  }
  function closeDrawer() {
    doc.body.classList.remove('nav-open');
    if (burger) burger.setAttribute('aria-expanded', 'false');
  }

  if (burger) {
    burger.addEventListener('click', function () {
      doc.body.classList.contains('nav-open') ? closeDrawer() : openDrawer();
    });
  }
  if (scrim) scrim.addEventListener('click', closeDrawer);
  doc.querySelectorAll('.drawer-nav a').forEach(function (a) {
    a.addEventListener('click', closeDrawer);
  });
  doc.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeDrawer();
  });
  window.addEventListener('resize', function () {
    if (window.innerWidth > 960) closeDrawer();
  });

  /* ======================================================================
     3. Scroll reveals
     ====================================================================== */
  var revealables = doc.querySelectorAll('.reveal');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    revealables.forEach(function (el) { io.observe(el); });
  }

  /* ======================================================================
     4a. Accordion
     ====================================================================== */
  doc.querySelectorAll('.acc-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = btn.closest('.acc');
      var panel = item.querySelector('.acc-panel');
      var open = item.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      panel.style.maxHeight = open ? panel.scrollHeight + 'px' : '';
    });
  });

  window.addEventListener('resize', function () {
    doc.querySelectorAll('.acc.is-open .acc-panel').forEach(function (p) {
      p.style.maxHeight = p.scrollHeight + 'px';
    });
  });

  /* ======================================================================
     4b. Back to top
     ====================================================================== */
  var toTop = doc.querySelector('.to-top');
  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  }

  /* ======================================================================
     4c. Enquiry form: front-end only, so it confirms and hands over
         the mailbox instead of pretending a message was sent.
     CONTACT_EMAIL is blank until the business shares an inbox to use;
     until then the form points people to the phone number instead.
     ====================================================================== */
  var CONTACT_EMAIL = '';
  var CONTACT_PHONE = '+974 3001 3636';
  var form = doc.querySelector('#enquiry-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var status = doc.querySelector('#form-status');
      var isAr = currentLang() === 'ar';
      var data = new FormData(form);
      var name = (data.get('name') || '').toString().trim();

      var body = [
        'Name: ' + (data.get('name') || ''),
        'Company: ' + (data.get('company') || ''),
        'Email: ' + (data.get('email') || ''),
        'Phone: ' + (data.get('phone') || ''),
        'Service: ' + (data.get('service') || ''),
        'Requirement:',
        (data.get('message') || '')
      ].join('\n'); 

      if (!CONTACT_EMAIL) {
        if (status) {
          status.textContent = isAr
            ? 'شكرًا لك' + (name ? ' يا ' + name : '') + '. يُرجى الاتصال بنا على ' + CONTACT_PHONE + ' لإتمام طلبك.'
            : 'Thanks' + (name ? ', ' + name : '') + '. Please call us on ' + CONTACT_PHONE + ' to complete your enquiry.';
          status.classList.add('is-visible');
        }
        return;
      }

      if (status) {
        status.textContent = isAr
          ? 'شكرًا لك' + (name ? ' يا ' + name : '') + '. سيفتح برنامج البريد لديك برسالة جاهزة.'
          : 'Thanks' + (name ? ', ' + name : '') + '. Your mail app will open with this enquiry ready to send.';
        status.classList.add('is-visible');
      }

      window.location.href = 'mailto:' + CONTACT_EMAIL
        + '?subject=' + encodeURIComponent('Enquiry: ' + (data.get('service') || 'Ironleaf Trading & Contracting'))
        + '&body=' + encodeURIComponent(body);
    });
  }

  /* ---------- current year ---------- */
  doc.querySelectorAll('.js-year').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
