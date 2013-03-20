"""
URLConf for Django user creation and authentication.

Recommended usage is a call to ``include()`` in your project's root
URLConf to include this URLConf for any URL beginning with
``/accounts/``.

"""

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^activate/(?P<activation_key>\w+)/$', 'user_creation.views.activate', name='activate'),
)
