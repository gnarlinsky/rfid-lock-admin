from django.views.generic.simple import redirect_to
from django.conf.urls import patterns, include, url
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # go directly to the admin page for the *application*
    url(r'^lock/$',redirect_to, {'url': '/lockadmin/djock_app/'}),

    # Uncomment the next line to enable the admin:
    url(r'^lockadmin/', include(admin.site.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
)


