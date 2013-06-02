from django.views.generic import list_detail
from django.views.generic.simple import redirect_to, direct_to_template
from django.conf.urls import patterns, include, url
from rfid_lock_management.models import RFIDkeycard, Door
from rfid_lock_management import views
from django.http import HttpResponse
from django.shortcuts import redirect

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
   # Password-reset: add "Forgotten your password?" link on
   # log-in page
   url(r'^admin/password_reset/$', 'django.contrib.auth.views.password_reset',
       name='admin_password_reset'),
   url(r'^admin/password_reset/done/$',
       'django.contrib.auth.views.password_reset_done'),
   url(r'^reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
       'django.contrib.auth.views.password_reset_confirm'),
   url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete'),

   # go directly to the admin page for the *application*
   url(r'^lockadmin/', include(admin.site.urls)),

   # keycard activation
   url(r'start_scan/(?P<lockuser_object_id>\d+)/$',
       views.initiate_new_keycard_scan),
   url(r'done_scan/(?P<new_scan_pk>\d+)/$',
       views.finished_new_keycard_scan),

   # Highchart of visitors
   url(r'^chart/', views.chartify),

   # keycard authentication
   url(r'checkdoor/(?P<doorid>\d+)/checkrfid/(?P<rfid>\w{10})/$',
       views.check),

   # Arduino requesting list of all allowed RFIDs for
   # specified door
   url(r'door/(?P<doorid>\d+)/getallowed/$',
       views.get_allowed_rfids),

   # Uncomment the admin/doc line below to enable admin documentation:
   # url(r'^admin/doc/',
   # include('django.contrib.admindocs.urls')),
)
