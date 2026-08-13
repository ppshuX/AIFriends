from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings

from web.views.user.account.cookies import (
    delete_refresh_token_cookie,
    set_refresh_token_cookie,
)


class RefreshTokenCookieTests(SimpleTestCase):
    @override_settings(DEBUG=True)
    def test_development_cookie_is_not_secure(self):
        response = HttpResponse()
        set_refresh_token_cookie(response, "token")
        cookie = response.cookies["refresh_token"]
        self.assertFalse(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")

    @override_settings(DEBUG=False)
    def test_production_cookie_is_secure(self):
        response = HttpResponse()
        set_refresh_token_cookie(response, "token")
        self.assertTrue(response.cookies["refresh_token"]["secure"])

    @override_settings(DEBUG=False)
    def test_delete_cookie_uses_same_security_attributes(self):
        response = HttpResponse()
        delete_refresh_token_cookie(response)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie["max-age"], 0)
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")
