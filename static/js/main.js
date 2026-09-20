/* ==========================================================================
   Ironleaf Trading & Contracting: site behaviour
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
     0. Logo loader: waits for the page, blasts the logo, reveals the content
     ====================================================================== */
  (function () {
    var loader = doc.getElementById('loader');
    var LOADER_MIN_MS = 1000;   // the logo stays on screen at least this long
    var finished = false;

    function removeLoader() {
      if (loader && loader.parentNode) loader.parentNode.removeChild(loader);
    }

    function finish() {
      if (finished) return;
      finished = true;
      root.classList.remove('js-loading');
      var video = doc.querySelector('.hero-video');
      if (video && video.paused && video.play) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
      if (!loader) return;
      var logo = loader.querySelector('.loader-logo');
      if (logo) logo.addEventListener('animationend', removeLoader);
      else removeLoader();
      loader.classList.add('is-blast');
    }

    // Hold the loader for LOADER_MIN_MS (measured from the start of the page load),
    // and never before the page itself has finished loading.
    function ready() {
      var minShow = reduceMotion ? 0 : LOADER_MIN_MS;
      var elapsed = window.performance ? performance.now() : minShow;
      setTimeout(finish, Math.max(0, minShow - elapsed));
    }

    if (!root.classList.contains('js-loading')) { removeLoader(); return; }
    if (doc.readyState === 'complete') ready();
    else window.addEventListener('load', ready);
  })();

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
     4c. Enquiry form: posts to Django (CSRF token, honeypot, signed
         timestamp and image captcha are all verified on the server).
         Without JavaScript the form still works as a normal POST.
     ====================================================================== */
  var form = doc.querySelector('#enquiry-form');
  if (form && window.fetch) {
    var status = doc.querySelector('#form-status');
    var captchaImg = doc.querySelector('#captcha-img');
    var captchaInput = doc.querySelector('#captcha');
    var submitBtn = form.querySelector('button[type="submit"]');

    var MSG = {
      sent: ['Thank you. Your enquiry has been sent and we will be in touch shortly.', 'شكرًا لك. تم إرسال طلبك وسنتواصل معك قريبًا.'],
      invalid: ['Please check the highlighted fields and try again.', 'يُرجى التحقق من الحقول المحددة والمحاولة مرة أخرى.'],
      need_contact: ['Please add an email or a phone number so we can reply.', 'يُرجى إضافة بريد إلكتروني أو رقم هاتف لنتمكن من الرد.'],
      spam: ['Please remove the links from your message and try again.', 'يُرجى إزالة الروابط من رسالتك والمحاولة مرة أخرى.'],
      captcha: ['The security code was incorrect or has expired. Please try the new code.', 'رمز التحقق غير صحيح أو انتهت صلاحيته. جرّب الرمز الجديد.'],
      too_fast: ['That was very quick. Please wait a moment and try again.', 'كان ذلك سريعًا جدًا. يُرجى الانتظار قليلًا والمحاولة مرة أخرى.'],
      expired: ['This form has expired. Please reload the page and try again.', 'انتهت صلاحية النموذج. يُرجى إعادة تحميل الصفحة والمحاولة مرة أخرى.'],
      rate_limited: ['Too many enquiries from your connection. Please try again later or call us.', 'عدد كبير من الطلبات من اتصالك. حاول لاحقًا أو اتصل بنا.'],
      email_failed: ['We could not send your enquiry right now. Please call or WhatsApp us on +974 6686 1283.', 'تعذّر إرسال طلبك الآن. يُرجى الاتصال بنا أو مراسلتنا عبر واتساب على +974 6686 1283.'],
      error: ['Something went wrong. Please reload the page and try again.', 'حدث خطأ ما. يُرجى إعادة تحميل الصفحة والمحاولة مرة أخرى.']
    };

    var say = function (code) {
      var pair = MSG[code] || MSG.error;
      if (!status) return;
      status.textContent = pair[currentLang() === 'ar' ? 1 : 0];
      status.classList.add('is-visible');
      status.classList.toggle('is-ok', code === 'sent');
      status.classList.toggle('is-error', code !== 'sent');
    };

    var refreshCaptcha = function () {
      if (captchaImg) captchaImg.src = captchaImg.getAttribute('data-src') + '?r=' + Date.now();
      if (captchaInput) captchaInput.value = '';
    };

    doc.querySelectorAll('[data-captcha-refresh]').forEach(function (btn) {
      btn.addEventListener('click', function () { refreshCaptcha(); if (captchaInput) captchaInput.focus(); });
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      form.querySelectorAll('[aria-invalid]').forEach(function (el) { el.removeAttribute('aria-invalid'); });
      if (submitBtn) submitBtn.disabled = true;

      fetch(form.getAttribute('action') || window.location.href, {
        method: 'POST',
        body: new FormData(form),
        credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
      }).then(function (res) {
        return res.json().catch(function () { return { ok: false, code: 'error', fields: [] }; });
      }).then(function (data) {
        say(data.code);
        (data.fields || []).forEach(function (name) {
          var el = form.elements[name];
          if (el) el.setAttribute('aria-invalid', 'true');
        });
        if (data.ok) form.reset();
        // The server consumed the captcha on these outcomes, so show a fresh one.
        if (data.ok || data.code === 'captcha' || data.code === 'email_failed') refreshCaptcha();
        if (status && status.scrollIntoView) status.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest' });
      }).catch(function () {
        say('error');
      }).then(function () {
        if (submitBtn) submitBtn.disabled = false;
      });
    });
  }

  /* ---------- current year ---------- */
  doc.querySelectorAll('.js-year').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
