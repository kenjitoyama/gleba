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
    apps.admin.tests

Purpose:
    This file contains some tests for Gleba.
"""
import random
import time
from django.test import TestCase, Client
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from apps.admin.models import *
from apps.weigh.views import add_box

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

class TestPicker(TestCase):
    def setUp(self):
        joe = User.objects.create_user('joe', 'joe@doe.com', 'doe')
        joe.is_staff = True
        joe.save()
        self.c = Client()
        login = self.c.login(username = 'joe', password = 'doe')
        self.assertTrue(login)

    def test_picker_avg_weight(self):
        # create a picker
        anna = Picker.objects.create(
            first_name = 'Anna',
            last_name = 'Hickmann',
            active = True,
            discharged = False
        )
        anna.save()
        variety = Variety.objects.get(id = 1)
        nr_of_boxes = 20
        total = 0.0
        # Create some boxes
        for i in range(nr_of_boxes):
            time_now = time.strftime('%Y-%m-%d %H:%M:%S', # timestamp
                                     time.localtime())
            initial_weight = random.uniform(
                variety.minimum_weight,
                variety.minimum_weight + variety.tolerance
            )
            total += initial_weight
            response = self.c.get('/add_box/', {
                'picker':         anna.id,
                'variety':        1,
                'batch':          1,
                'initial_weight': initial_weight,
                'final_weight':   initial_weight + 0.1,
                'timestamp':      time_now,
            })
            # make sure every request is successful
            self.assertEquals(response.status_code, 200)
        # check our average with the picker's average
        # round() is used to eliminate precision errors
        self.assertEquals(
            round(total/nr_of_boxes, 6), # 6 decimal digits
            round(anna.get_avg_init_weight(), 6)
        )

