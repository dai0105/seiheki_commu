from django.conf import settings

def r2_settings(request):
    return {
        'R2_BASE_URL': settings.R2_BASE_URL,
    }