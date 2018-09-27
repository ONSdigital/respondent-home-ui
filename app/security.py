import random
import string

from aiohttp import web


DEFAULT_RESPONSE_HEADERS = {
    'Strict-Transport-Security': ['max-age=31536000', 'includeSubDomains'],
    'Content-Security-Policy': {
        'default-src': ["'self'", 'https://cdn.ons.gov.uk'],
        'font-src': ["'self'", 'data:', 'https://cdn.ons.gov.uk'],
        'script-src': ["'self'", 'https://www.google-analytics.com', 'https://cdn.ons.gov.uk'],
        'connect-src': ["'self'", 'https://www.google-analytics.com', 'https://cdn.ons.gov.uk'],
        'img-src': ["'self'", 'data:', 'https://www.google-analytics.com', 'https://cdn.ons.gov.uk'],
    },
    'X-XSS-Protection': '1',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'same-origin',
}

ADD_NONCE_SECTIONS = ['script-src', ]


rnd = random.SystemRandom()


def get_random_string(length):
    allowed_chars = (
            string.ascii_lowercase +
            string.ascii_uppercase +
            string.digits)
    return ''.join(
        rnd.choice(allowed_chars)
        for _ in range(length))


@web.middleware
async def nonce_middleware(request, handler):
    request.csp_nonce = get_random_string(16)
    return await handler(request)


async def on_prepare(request: web.BaseRequest, response: web.StreamResponse):
    for header, value in DEFAULT_RESPONSE_HEADERS.items():
        if isinstance(value, dict):
            value = '; '.join([
                f"{section} {' '.join(content)} 'nonce-{request.csp_nonce}'"
                if section in ADD_NONCE_SECTIONS else
                f"{section} {' '.join(content)}"
                for section, content in value.items()])
        elif not isinstance(value, str):
            value = ' '.join(value)
        response.headers[header] = value
