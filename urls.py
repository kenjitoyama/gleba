from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('gleba.glebaAdmin.views',
    # csv
    (r'^csv/$', 'generate_csv_range')
)

# DB related
urlpatterns += patterns('gleba.apps.weigh.views',
    (r'^addBox/$', 'addBox'),
    (r'^pickerList/$', 'getPickerList'),
    (r'^pickerList.xml$', 'getPickerListXML'),
    (r'^batchList/$', 'getBatchList'),
    (r'^batchList.xml$', 'getBatchListXML'),
    (r'^varietyList/$', 'getVarietyList'),
    (r'^varietyList.xml$', 'getVarietyListXML'),
)

# Reports
urlpatterns += patterns('gleba.apps.report.views',
    (r'^report/$', 'generate_report'),
    (r'^report/picker/(\d+)/$', 'generate_report_picker'),
    (r'^report/picker/$', 'generate_report_all_picker'),
    (r'^report/flush/(\d+)/$', 'generate_report_flush'),
    (r'^report/crop/(\d+)/$', 'generate_report_crop'),
    (r'^report/room/(\d+)/$', 'generate_report_room'),
)

urlpatterns += patterns(
    # Bundies
    'gleba.apps.bundy.views',
    (r'^bundy/(\d+)/$', 'bundy'),
    (r'^bundy/$', 'bundy')
)

urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^admin/', include(admin.site.urls)),
    (r'^$', include(admin.site.urls)),
)
