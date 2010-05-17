from django.conf.urls.defaults import *
import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^animation\/?', include('animation.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^', include('mediasync.urls')),    
)


if settings.DEBUG:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]    
    urlpatterns += patterns('', (r'^%s(?P<path>.*)$' % _media_url, serve, { 'document_root': settings.MEDIA_ROOT }))
   