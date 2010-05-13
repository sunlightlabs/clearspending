from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

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
    (r'^$', 'direct_to_template', {'template':'index.html'})
)
