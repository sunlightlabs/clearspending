import random
import os
from datetime import date

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

ROWS_PER_CYCLE = 500000

# determines CSV order
CANONICAL_FIELD_ORDER = [
	'fyq',
	'cfda_program_num',
	'sai_number',
	'recipient_name',
	'recipient_city_code',
	'recipient_city_name',
	'recipient_county_code',
	'recipient_county_name',
	'recipient_state_code',
	'recipient_zip',
	'recipient_type',
	'action_type',
	'recipient_cong_district',
	'agency_code',
	'federal_award_id',
	'federal_award_mod',
	'fed_funding_amount',
	'non_fed_funding_amount',
	'total_funding_amount',
	'obligation_action_date',
	'starting_date',
	'ending_date',
	'assistance_type',
	'record_type',
	'correction_late_ind',
	'fyq_correction',
	'principal_place_code',
	'principal_place_state',
	'principal_place_cc',
	'principal_place_zip',
	'principal_place_cd',
	'cfda_program_title',
	'agency_name',
	'recipient_state_name',
	'project_description',
	'duns_no',
	'duns_conf_code',
	'progsrc_agen_code',
	'progsrc_acnt_code',
	'progsrc_subacnt_code',
	'receip_addr1',
	'receip_addr2',
	'receip_addr3',
	'face_loan_guran',
	'orig_sub_guran',
	'parent_duns_no',
	'record_id',
	'fiscal_year',
	'principal_place_state_code',
	'award_id',
	'recip_cat_type',
	'asst_cat_type',
	'recipient_cd',
	'maj_agency_cat',
	'mod_name',
	'recip_id',
	'business_identifier',
	'rec_flag',
    'recipient_country_code',
    'principal_place_country_code',
    'uri',
    'lookup_parent_rec_id'
]

# database settings for USASpending data, not django project database settings
PG_USER = ''
PG_PASSWORD = ''
PG_HOST = ''
PG_DATABASE = ''
PG_TABLE_NAME = 'grants_grant'
PG_PORT = 5432
# TODO: add clauses eliminating nonfinancial programs & summary-level programs
PG_WHERE_CLAUSE = "fiscal_year IN (2009, 2010, 2011)"

#for contact form
EMAIL_HOST = ''
#EMAIL_PORT = '25'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
#EMAIL_USE_TLS = 'True'




# Django settings for faads_scorecard project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '',
        'USER': '', 
        'PASSWORD': '',
        'HOST': 'localhost',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Eastern'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, '..', '.static'))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

#since we're under the foundation site we use this url prefix instead ofthe root
SUB_SITE = 'clearspending' 
 
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = 'http://assets.sunlightfoundation.com/admin/8961/'

# Set this in your local_settings.py to something not generated at runtime
SECRET_KEY_CHARS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxy'
SECRET_KEY = ''.join([SECRET_KEY_CHARS[random.randint(0, len(SECRET_KEY_CHARS)-1)]
                      for _ in range(50)])

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
CACHE_MIDDLEWARE_SECONDS = (60 * 60 * 24)
CACHE_MIDDLEWARE_KEY_PREFIX = ''

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',    
    'cfda',
    'completeness',
    'consistency',
    'timeliness',
    'metrics',
    'animation',
    'django.contrib.humanize',
    'helpers',
    'haystack'
)


#these are the fiscal years we want to calculate metrics for
FISCAL_YEARS = [2009, 2010, 2011]

# Threshold for consideration of spending transactions. In order to 
# facilitate comparisons between the timeliness each fiscal year,
# set this to the number of days between the end of the latest fiscal 
# year and the day on which you are running the timeliness parser.
FISCAL_YEAR_LAG_THRESHOLD = (date.today() - date(year=max(FISCAL_YEARS), month=9, day=30)).days

GRAPH_DIR = MEDIA_ROOT + '/images/charts/'   #should be overridden by local settings maybe?

HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = ''

try:
    from local_settings import *
except Exception, e:
    pass
