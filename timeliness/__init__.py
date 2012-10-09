import urllib
import urllib2
import re
import os
import csv
import cPickle as pickle
from timeliness.cube import Cube
from BeautifulSoup import BeautifulSoup
from datetime import date    
from metrics.models import ProgramTimeliness, AgencyTimeliness
from cfda.models import Program, Agency
from django.conf import settings

DATA_DIR = "timeliness_data"
DOWNLOAD_DIR = os.path.join(DATA_DIR, 'raw')
FISCAL_YEARS = settings.FISCAL_YEARS

 
    
