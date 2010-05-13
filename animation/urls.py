from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('', 
    url(r'^$', 'animation.views.main', {}, name='animation'),    
)
