from django.conf.urls.defaults import *
import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^%s/' % settings.SUB_SITE, include('clearspending_urls')),
    url(r'^', include('mediasync.urls')),    
)

   




