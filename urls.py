from django.conf.urls.defaults import *
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^%s/' % settings.SUB_SITE, include('clearspending_urls')),
    url(r'^', include('mediasync.urls')),    
)

#if settings.DEBUG:
#    from django.views.static import serve
#    _media_url = settings.MEDIA_URL
#    if _media_url.startswith('/'):
#        _media_url = _media_url[1:]    
#    urlpatterns += patterns('', (r'^%s(?P<path>.*)$' % _media_url, serve, { 'document_root': settings.MEDIA_ROOT }))
   




