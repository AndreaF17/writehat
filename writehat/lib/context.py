from django.conf import settings


def writehat_ui(request):
    return {
        'SSO_ENABLED': bool(getattr(settings, 'SSO_ENABLED', False)),
        'SSO_DISPLAY_NAME': str(getattr(settings, 'SSO_DISPLAY_NAME', 'Single Sign-On')),
    }
