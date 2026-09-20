"""
Self-hosted image captcha, validated entirely on the server.

* The answer never reaches the browser: only a distorted PNG is sent, and the
  session stores a salted HMAC of the code.
* Codes are single use. Any verification attempt consumes the challenge, so a
  bot cannot keep guessing against the same image.
* Codes expire (CAPTCHA_TTL_SECONDS) and are generated with `secrets`.
"""
import hashlib
import hmac
import io
import math
import random
import secrets
import time

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

# No I, L, O, 0 or 1: they are easy to confuse once distorted.
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
SESSION_KEY = "contact_captcha"
THROTTLE_KEY = "contact_captcha_issued"
WIDTH, HEIGHT = 220, 80


def _digest(code, salt):
    return hmac.new(settings.SECRET_KEY.encode(), (salt + code).encode(), hashlib.sha256).hexdigest()


def issue(request):
    """Create a fresh challenge for this session and return the plain code."""
    code = "".join(secrets.choice(ALPHABET) for _ in range(settings.CAPTCHA_LENGTH))
    salt = secrets.token_hex(8)
    request.session[SESSION_KEY] = {"d": _digest(code, salt), "s": salt, "t": int(time.time())}
    return code


def verify(request, answer):
    """Check the visitor's answer. Always consumes the stored challenge."""
    data = request.session.pop(SESSION_KEY, None)
    if not data or not answer:
        return False
    if time.time() - data.get("t", 0) > settings.CAPTCHA_TTL_SECONDS:
        return False
    cleaned = "".join(str(answer).split()).upper()
    return hmac.compare_digest(_digest(cleaned, data["s"]), data["d"])


def allow_new_image(request):
    """Cap how many codes one session can request (stops image scraping)."""
    now = time.time()
    issued = [t for t in request.session.get(THROTTLE_KEY, []) if now - t < 600]
    if len(issued) >= settings.CAPTCHA_IMAGE_LIMIT:
        request.session[THROTTLE_KEY] = issued
        return False
    issued.append(now)
    request.session[THROTTLE_KEY] = issued
    return True


def _font(size):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def render_png(code):
    """Draw the code as a clear PNG with light noise and a gentle wave."""
    rnd = random.SystemRandom()
    img = Image.new("RGB", (WIDTH, HEIGHT), (244, 246, 250))
    draw = ImageDraw.Draw(img)

    for _ in range(140):
        tone = rnd.randint(190, 225)
        draw.point((rnd.randrange(WIDTH), rnd.randrange(HEIGHT)), fill=(tone, tone, tone + 8))

    font = _font(50)
    step = (WIDTH - 40) / len(code)
    x = 22.0
    for ch in code:
        tile = Image.new("RGBA", (72, 76), (0, 0, 0, 0))
        ImageDraw.Draw(tile).text(
            (14, 6), ch, font=font,
            fill=(rnd.randint(10, 40), rnd.randint(25, 55), rnd.randint(70, 110), 255),
        )
        tile = tile.rotate(rnd.uniform(-10, 10), resample=Image.BICUBIC, expand=True)
        img.paste(tile, (int(x), rnd.randint(-1, 4)), tile)
        x += step

    # Two faint strike-through lines: enough to defeat naive OCR without hurting readability.
    for _ in range(2):
        draw.line(
            [(0, rnd.randrange(20, HEIGHT - 20)), (WIDTH, rnd.randrange(20, HEIGHT - 20))],
            fill=(rnd.randint(170, 200), rnd.randint(170, 200), rnd.randint(180, 210)),
            width=1,
        )

    warped = Image.new("RGB", (WIDTH, HEIGHT), (244, 246, 250))
    amp, period, phase = rnd.uniform(1.5, 2.5), rnd.uniform(26, 36), rnd.uniform(0, math.tau)
    for col in range(WIDTH):
        shift = int(amp * math.sin(col / period * math.tau / 2 + phase))
        warped.paste(img.crop((col, 0, col + 1, HEIGHT)), (col, shift))

    buf = io.BytesIO()
    warped.save(buf, "PNG", optimize=True)
    return buf.getvalue()
