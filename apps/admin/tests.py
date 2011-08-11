"""
Copyright (C) Simon Dawson, Kenji Toyama, Meryl Baquiran, Chris Ellis 2010-2011
This file is part of Gleba 

Gleba is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Gleba is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Gleba.  If not, see <http://www.gnu.org/licenses/>.

Author(s):
    Simon Dawson
    Daniel Kenji Toyama

Path: 
    gleba.apps.admin.tests

Purpose:
    This file contains some tests for Gleba.
"""
from django.test import TestCase
from django.shortcuts import get_object_or_404
from django.test import Client
from django.contrib.auth.models import User
from apps.admin.models import *

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
