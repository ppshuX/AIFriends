from django.conf import settings


REFRESH_TOKEN_COOKIE = 'refresh_token'
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60


def cookie_options():
    return {
        'httponly': True,
        'samesite': 'Lax',
        'secure': not settings.DEBUG,
        'path': '/',
    }


def set_refresh_token_cookie(response, token):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=str(token),
        max_age=REFRESH_TOKEN_MAX_AGE,
        **cookie_options(),
    )


def delete_refresh_token_cookie(response):
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value='',
        max_age=0,
        expires='Thu, 01 Jan 1970 00:00:00 GMT',
        **cookie_options(),
    )
