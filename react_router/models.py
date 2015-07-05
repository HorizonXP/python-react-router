# Django hook to configure settings on startup

from django.conf import settings
import react_router.conf

react_router.conf.settings.configure(
    **getattr(settings, 'REACT_ROUTER', {})
)
