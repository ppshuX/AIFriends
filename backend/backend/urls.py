"""
URL configuration for backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.urls')),
]

# Portable single-process server: always serve frontend assets / django static / media.
# django.conf.urls.static.static() is a no-op when DEBUG=False; runserver auto-static
# also does not apply under waitress.
urlpatterns += [
    re_path(
        r'^assets/(?P<path>.*)$',
        serve,
        {'document_root': settings.BASE_DIR / 'static' / 'frontend' / 'assets'},
    ),
    re_path(
        r'^static/(?P<path>.*)$',
        serve,
        {'document_root': settings.BASE_DIR / 'static'},
    ),
    re_path(
        r'^media/(?P<path>.*)$',
        serve,
        {'document_root': settings.MEDIA_ROOT},
    ),
]
