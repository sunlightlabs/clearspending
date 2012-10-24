from django.conf import settings

def common_context(request):
    return {
        'FISCAL_YEARS': settings.FISCAL_YEARS,
        'FISCAL_YEARS_UNICODE': [unicode(fy) for fy in settings.FISCAL_YEARS],
        'MIN_YEAR': min(settings.FISCAL_YEARS),
        'MAX_YEAR': max(settings.FISCAL_YEARS)
    }

