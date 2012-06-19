from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Database interaction
urlpatterns = patterns('apps.weigh.views',
    (r'^add_boxes/$'             , 'add_boxes'),
    (r'^picker_list.json$',  'get_picker_list'),
    (r'^batch_list.json$',   'get_batch_list'),
    (r'^variety_list.json$', 'get_variety_list'),
)

# Production Reports
urlpatterns += patterns('apps.report.views',
    (r'^report/$', 'generate_report'),
    (r'^report/picker/(\d+)/$', 'generate_report_picker'),
    (r'^report/picker/(\d+)/report.html$', 'picker_report_page'),
    (r'^report/picker/(\d+)/daily_totals.json$', 'daily_totals'),
    (r'^report/picker/(\d+)/daily_hours.json$', 'daily_hours'),
    (r'^report/picker/$', 'generate_report_all_picker'),
    (r'^report/flush/(\d+)/$', 'generate_report_flush'),
    (r'^report/crop/(\d+)/$', 'generate_report_crop'),
    (r'^report/room/(\d+)/$', 'generate_report_room'),
)

# CSV timesheet reporting
urlpatterns += patterns('apps.report.csv_views',
    (r'^report/csv/$', 'generate_csv_range')
)

# Bundies
urlpatterns += patterns('apps.bundy.views',
    (r'^bundy/(\d+)/$', 'bundy'),
    (r'^bundy/$', 'bundy')
)

urlpatterns += patterns('',
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^$', include(admin.site.urls)),
)
