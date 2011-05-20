from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('gleba.glebaAdmin.views',
    # DB related
    (r'^addBox/$', 'addBox'),
    (r'^pickerList/$', 'getPickerList'),
    (r'^pickerList.xml$', 'getPickerListXML'),
    (r'^batchList/$', 'getBatchList'),
    (r'^batchList.xml$', 'getBatchListXML'),
    (r'^varietyList/$', 'getVarietyList'),
    (r'^varietyList.xml$', 'getVarietyListXML'),
    
    # Reports
    (r'^report/$', 'generate_report'),
    (r'^report/picker/(\d+)/$', 'generate_report_picker'),
    (r'^report/picker/$', 'generate_report_all_picker'),
    (r'^report/flush/(\d+)/$', 'generate_report_flush'),
    (r'^report/crop/(\d+)/$', 'generate_report_crop'),
    (r'^report/room/(\d+)/$', 'generate_report_room'),

    # Bundies
    (r'^bundy/(\d+)/$', 'bundy'),
    (r'^bundy/$', 'bundy'),

    # csv
    (r'^csv/$', 'generate_csv_range'),
)

urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^admin/', include(admin.site.urls)),
    (r'^$', include(admin.site.urls)),
)
