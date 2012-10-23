from django.conf import settings

def common_context(request):
    return {
        'FISCAL_YEARS': settings.FISCAL_YEARS
    }

