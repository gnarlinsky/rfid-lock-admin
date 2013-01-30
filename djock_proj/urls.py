from django.views.generic.simple import redirect_to, direct_to_template
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the next line to enable the admin:
    url(r'^lockadmin/', include(admin.site.urls)),

    # go directly to the admin page for the *application*
    url(r'^lock/$',redirect_to, {'url': '/lockadmin/djock_app/'}),

    # is this rfid allowed to access this door
    # (keeping door identifier just numerical for now)
    # (direct_to_template right now, just a quick demo of displaying arguments in the url,
    #   in an HTML template... Not actually performing the check yet... So will need a view. 
    # [ But since all I have to send back is a 1 or 0, maybe I don't have to write a template at all?])
    # direct_to_template passes the dictionary 'params' to the template, so to
    #   access 'doorid,' for example, you have to do {{ params.doorid }} )
    url(r'door/(?P<doorid>\d+)/checkrfid/(?P<rfid>.{2})/$', direct_to_template, {'template': 'basic.html' }  ),
    #(just going with a 2 digit "rfid" right now to make my lazy life easier)

    # get list of rfid's allowed to open this door
    # direct_to_template right now, just a quick demo of displaying arguments in the url,
    # not displaying the objects yet
    # (later, in view, something like -
    #   return HttpResponse(data, mimetype='application/json')
    #url(r'^door/(?P<doorid>\d+)/getallowed/$', direct_to_template, {'template': 'we_are_ok.html' }    ),
    url(r'^door/(?P<doorid>\d+)/getallowed/$', direct_to_template, {'template': 'admin/we_are_ok.html' }    ),
    url(r'door/(?P<doorid>\d+)/getallowed/$', direct_to_template, {'template': 'admin/we_are_ok.html' }    ),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # testing stuff/temp
    url(r'^t/$', direct_to_template, {'template': 'test/index.html' }    ),
    #url(r'fake/$', 'djock_app.views.fake_assign' ), 

)


