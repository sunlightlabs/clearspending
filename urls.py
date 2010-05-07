from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^animation\/?', include('animation.urls')),
    # Example:
    # (r'^faads_scorecard/', include('faads_scorecard.foo.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include('admin.site.urls')),
    (r'^', include('mediasync.urls')),    
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_MEDIA_DIR}),
    )