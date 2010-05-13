from django.conf.urls.defaults import *
<<<<<<< HEAD:urls.py
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list
=======
import settings
from django.contrib import admin
>>>>>>> 83f80c997ce128d233017eb603f3f3f3185ba611:urls.py

admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^scorecard/agency/(?P<agency_id>\d+)/', 'metrics.views.get_agency_detail'),
    (r'^scorecard/program/(?P<program_id>\d+)/', 'metrics.views.get_program_detail'),
    (r'^scorecard/$', 'metrics.views.scorecard'),
    (r'^analysis/', 'direct_to_template', {'template': 'analysis.html'}),
    (r'^methodology/', 'direct_to_template', {'template': 'methodology,html'}),
    (r'^background/', 'direct_to_template', {'template': 'background.html'}),
    (r'^corrections/', 'object_list', {'template': 'corrections.html'}),
    (r'^$', 'direct_to_template', {'template':'index.html'}),
    (r'^animation\/?', include('animation.urls')),
    (r'^admin/', include('admin.site.urls')),
    (r'^', include('mediasync.urls')),    
)


if settings.DEBUG:
    from django.views.static import serve
    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]    
    urlpatterns += patterns('', (r'^%s(?P<path>.*)$' % _media_url, serve, { 'document_root': settings.MEDIA_ROOT }))
   
