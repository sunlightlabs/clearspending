from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
#    (r'^scorecard/agency/(?P<agency_id>\d+)/', 'metrics.views.get_agency_detail'),
#    (r'^scorecard/program/(?P<program_id>\d+)/', 'metrics.views.get_program_detail'),
#    (r'^scorecard/$', 'metrics.views.scorecard'),

    (r'^analysis/', direct_to_template, {'template': 'analysis.html'}),
    (r'^methodology/', direct_to_template, {'template': 'methodology,html'}),
    (r'^background/', direct_to_template, {'template': 'background.html'}),
    (r'^corrections/', object_list, {'template': 'corrections.html'}),
    (r'^animation\/?', include('animation.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^agency/(?P<agency_id>\d+)/(?P<fiscal_year>\d{4})/(?P<unit>\w+)/', 'metrics.views.agencyDetail'),
    (r'^program/(?P<program_id>\d+)/(?P<unit>\w+)/', 'metrics.views.programDetail'), 
    (r'^$', direct_to_template, {'template':'index.html'}),
    (r'^', include('mediasync.urls')),    
)


#if settings.DEBUG:
#    from django.views.static import serve
#    _media_url = settings.MEDIA_URL
#    if _media_url.startswith('/'):
#        _media_url = _media_url[1:]    
#    urlpatterns += patterns('', (r'^%s(?P<path>.*)$' % _media_url, serve, { 'document_root': settings.MEDIA_ROOT }))
   




