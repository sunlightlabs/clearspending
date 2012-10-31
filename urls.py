from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list
from metrics.models import ProgramCorrection
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
#    (r'^scorecard/agency/(?P<agency_id>\d+)/', 'metrics.views.get_agency_detail'),
#    (r'^scorecard/program/(?P<program_id>\d+)/', 'metrics.views.get_program_detail'),
    url(r'^consistency/$', 'metrics.views.consistency', name='consistency'),
    url(r'^timeliness/$', 'metrics.views.timeliness', name='timeliness'),
    url(r'^timeliness/(?P<fiscal_year>\d{4})/$', 'metrics.views.agency_timeliness_data'),
    url(r'^completeness/$', 'metrics.views.completeness', name='completeness'),
    url(r'^completeness/(?P<fiscal_year>\d{4})/$', 'metrics.views.agency_completeness_data'),
    url(r'^scorecard/$', 'metrics.views.index', name='scorecard-index'),
    url(r'^scorecard/(?P<unit>\w+)/(?P<fiscal_year>\d{4})/', 'metrics.views.index', name='scorecard-index-extra'),
    url(r'^bestprograms/(?P<fiscal_year>\d{4})/', 'metrics.views.list_best_programs', name='list-best-programs'),
    url(r'^results/', direct_to_template, {'template': 'analysis.html'}, name='analysis' ),
    url(r'^results-consistency/', direct_to_template, {'template': 'results-consistency.html'}, name='results-consistency' ),
    url(r'^results-completeness/', direct_to_template, {'template': 'results-completeness.html'}, name='results-completeness' ),
    url(r'^results-timeliness/', direct_to_template, {'template': 'results-timeliness.html'}, name='results-timeliness' ),
    url(r'^data-act/', direct_to_template, {'template': 'data-act.html'}, name='data-act' ),
    url(r'^summary/$', direct_to_template, {'template': 'summary.html'}, name='summary' ),
    url(r'^methodology/', direct_to_template, {'template': 'methodology.html'}, name='methodology'),
    url(r'^press/$', direct_to_template, {'template': 'media.html'}, name='media-index'),
    url(r'^background/', direct_to_template, {'template': 'background.html'}, name='background'),
    url(r'^resources/', direct_to_template, {'template': 'resources.html'}, name='resources'),
    url(r'^feedback/$', direct_to_template, {'template':'contact.html'}, name='feedback'),
    url(r'^feedback/submitted/$', 'metrics.views.contact', name="contact-post"),
    url(r'^corrections/', object_list, {'template_name': 'corrections.html', 'queryset': ProgramCorrection.objects.all().order_by('program')}, name='corrections'),
    url(r'^animation/$', direct_to_template, {'template': 'animation/index.html'}, name="animation"),
    url(r'^agency/(?P<agency_id>\d+)/(?P<fiscal_year>\d{4})/(?P<unit>\w+)/', 'metrics.views.agencyDetail', name="agency_detail"),
    url(r'^program/(?P<cfda_number>\d{2}\.\d{3})/(?P<unit>\w+)/', 'metrics.views.programDetail', name='program_detail_by_cfda'),
    url(r'^program/(?P<program_id>\d+)/(?P<unit>\w+)/', 'metrics.views.programDetail', name='program_detail'),
    url(r'^search/(?P<search_string>[\w\+%\d\s]+)/(?P<unit>\w+)/(?P<fiscal_year>\d{4})/', 'metrics.views.search_results', name='search-request'),
    url(r'^search/', 'metrics.views.search_query', name='search-query'),
    url(r'^$', direct_to_template, {'template':'index.html'}, name='clearspending-index'),
)

if settings.SUB_SITE:
    urlpatterns = patterns('',
        url(r'^clearspending/', include(urlpatterns))
    )
