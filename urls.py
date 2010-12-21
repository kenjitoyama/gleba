from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^gleba/', include('gleba.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^addBox/$', 'gleba.glebaAdmin.views.addBox'),
    (r'^pickerList/$', 'gleba.glebaAdmin.views.getPickerList'),
    (r'^batchList/$', 'gleba.glebaAdmin.views.getBatchList'),
    (r'^varietyList/$', 'gleba.glebaAdmin.views.getVarietyList'),
    (r'^report/$', 'gleba.glebaAdmin.views.generateReport'),
    (r'^report/picker/(\d+)/$', 'gleba.glebaAdmin.views.generateReportPickerRange'),
    (r'^report/flush/(\d+)/$', 'gleba.glebaAdmin.views.generateReportFlushRange'),
    (r'^report/crop/(\d+)/$', 'gleba.glebaAdmin.views.generateReportCropRange'),
    (r'^report/room/(\d+)/$', 'gleba.glebaAdmin.views.generateReportRoomRange'),
    (r'^bundy/$', 'gleba.glebaAdmin.views.bundy'),
    (r'^bundy/(signon|signoff|confirm)/(\d+)/$', 'gleba.glebaAdmin.views.bundyOnOff'),
    (r'^csv/$', 'gleba.glebaAdmin.views.generateCSVRange'),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'', include(admin.site.urls)),
)
