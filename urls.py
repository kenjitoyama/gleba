from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Database interaction
urlpatterns = patterns('gleba.apps.weigh.views',
    (r'^addBox/$', 'addBox'),
    (r'^pickerList/$', 'getPickerList'),
    (r'^picker_list.xml$', 'get_picker_list_xml'),
    (r'^picker_list.json$', 'get_picker_list_json'),
    (r'^batchList/$', 'getBatchList'),
    (r'^batch_list.xml$', 'get_batch_list_xml'),
    (r'^batch_list.json$', 'get_batch_list_json'),
    (r'^varietyList/$', 'getVarietyList'),
    (r'^varietyList.xml$', 'getVarietyListXML'),
    (r'^variety_list.json$', 'get_variety_list_json'),
)

# Production Reports
urlpatterns += patterns('gleba.apps.report.views',
    (r'^report/$', 'generate_report'),
    (r'^report/picker/(\d+)/$', 'generate_report_picker'),
    (r'^report/picker/$', 'generate_report_all_picker'),
    (r'^report/flush/(\d+)/$', 'generate_report_flush'),
    (r'^report/crop/(\d+)/$', 'generate_report_crop'),
    (r'^report/room/(\d+)/$', 'generate_report_room'),
)

# CSV timesheet reporting
urlpatterns += patterns('gleba.apps.report.csv_views',
    (r'^report/csv/$', 'generate_csv_range')
)

# Bundies
urlpatterns += patterns('gleba.apps.bundy.views',
    (r'^bundy/(\d+)/$', 'bundy'),
    (r'^bundy/$', 'bundy')
)

urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^admin/', include(admin.site.urls)),
    (r'^$', include(admin.site.urls)),
)
