"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.shortcuts import get_object_or_404
from django.test import Client
from django.contrib.auth.models import User
from glebaAdmin.models import *
from glebaAdmin.views import *

################################################################################
# View tests
################################################################################

class TestReportViews(TestCase):
    def setUp(self):
        joe = User.objects.create_user('joe', 'joe@doe.com', 'doe')
        joe.is_staff = True
        joe.save()
        self.c = Client()
        login = self.c.login(username = 'joe', password = 'doe')
        self.assertTrue(login)
        self.picker = get_object_or_404(Picker, pk = 1)

    def test_views_daily_totals(self):
        variety = get_object_or_404(Variety, pk = 1)
        batch = get_object_or_404(Batch, pk = 1)
        # Create some boxes
        for i in range(20):
            timestamp = datetime.datetime(2011, 05, i+10)
            for j in range(1000):
                box = Box(initialWeight = 4.050 + j,
                          finalWeight = 4.025,
                          timestamp = timestamp,
                          contentVariety = variety,
                          picker = self.picker,
                          batch = batch)
                box.save()
        start_date = datetime.datetime(2011, 05, 01)
        end_date = datetime.datetime(2011, 05, 11)
        daily_totals = self.picker.daily_totals(start_date, end_date)
        self.assertEquals(len(daily_totals), 1)
        # test the report view
        for i in range(20000):
            self.c.post('/report/picker/1', {
                'startDate': '01-05-2011',
                'endDate':   '11-05-2011',
            })
